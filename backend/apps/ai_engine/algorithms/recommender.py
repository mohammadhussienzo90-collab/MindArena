"""
Hybrid Recommendation Engine
==============================
Six-signal recommendation system for selecting optimal next challenges.

Signal weights
--------------
1. IRT optimal difficulty   30 %
2. BKT knowledge gaps       25 %
3. Content-based filtering  15 %  (personality-trait alignment)
4. FSRS due cards           10 %
5. Thompson Sampling bandit 10 %
6. Random exploration       10 %

References
----------
- Baker, F.B. & Kim, S. (2004). *Item Response Theory* (2nd ed.).
- Corbett, A.T. & Anderson, J.R. (1995). Knowledge tracing.
- Pimsleur, P. (1967). A memory schedule (spaced repetition).
- Thompson, W.R. (1933). On the likelihood that one unknown probability
  exceeds another in view of two samples.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

from django.db.models import Count, Q
from django.utils import timezone


# ======================================================================
# Constants
# ======================================================================
TRAIT_FIELDS: Tuple[str, ...] = (
    'openness', 'conscientiousness', 'extraversion', 'agreeableness',
    'neuroticism', 'self_awareness', 'empathy', 'emotional_regulation',
    'social_skills', 'analytical_thinking', 'creative_thinking',
    'practical_thinking', 'risk_tolerance',
)

SIGNAL_WEIGHTS: Dict[str, float] = {
    'irt': 0.30,
    'bkt': 0.25,
    'content': 0.15,
    'fsrs': 0.10,
    'thompson': 0.10,
    'exploration': 0.10,
}


# ======================================================================
# Helper: cosine similarity
# ======================================================================
def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two equal-length numeric vectors.

    Returns 0.0 when either vector has zero magnitude.
    """
    if len(vec_a) != len(vec_b):
        raise ValueError(
            f"Vectors must have equal length ({len(vec_a)} != {len(vec_b)})"
        )
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ======================================================================
# Helper: trait vector extraction
# ======================================================================
def _assessment_trait_vector(assessment) -> List[float]:
    """Extract the 13-dimensional trait vector from a PersonalityAssessment."""
    return [getattr(assessment, field, 50.0) for field in TRAIT_FIELDS]


def _challenge_trait_vector(challenge) -> List[float]:
    """Build a 13-d trait vector for a Challenge.

    Primary trait receives a weight of 100, secondary trait receives 60,
    and any additional trait_points are overlaid.  All other dimensions
    default to 0.
    """
    vec = [0.0] * len(TRAIT_FIELDS)
    field_index = {f: i for i, f in enumerate(TRAIT_FIELDS)}

    # Primary / secondary traits from the Challenge model
    if challenge.primary_trait in field_index:
        vec[field_index[challenge.primary_trait]] = 100.0
    if challenge.secondary_trait and challenge.secondary_trait in field_index:
        vec[field_index[challenge.secondary_trait]] = 60.0

    # Overlay any explicit trait_points stored in JSON
    if challenge.trait_points:
        for trait, value in challenge.trait_points.items():
            if trait in field_index:
                vec[field_index[trait]] = float(value)

    return vec


# ======================================================================
# Signal 1: IRT optimal difficulty
# ======================================================================
def _irt_score(player_ability: float, challenge_difficulty: int) -> float:
    """Score a challenge by how close its difficulty is to the player's
    zone of proximal development (IRT 2PL model).

    The optimal item difficulty is where the player has a ~70 % chance of
    success -- this maximises information gain.

    Parameters
    ----------
    player_ability : float
        Player theta on the IRT scale (typically -3 to +3).
    challenge_difficulty : int
        Challenge difficulty 1-10 mapped to IRT beta via linear transform.

    Returns
    -------
    float
        0-1 score (1 = perfectly matched difficulty).
    """
    # Map 1-10 difficulty to IRT beta scale (-3 to +3)
    beta = (challenge_difficulty - 5.5) * (6.0 / 9.0)
    # 2PL probability with discrimination a = 1.0
    p_correct = 1.0 / (1.0 + math.exp(-(player_ability - beta)))
    # Optimal probability is 0.70; penalise deviations
    return max(0.0, 1.0 - abs(p_correct - 0.70) / 0.30)


# ======================================================================
# Signal 2: BKT knowledge gaps
# ======================================================================
def _bkt_score(player, challenge) -> float:
    """Score by how much a challenge addresses the player's weakest skills.

    Challenges targeting traits where the player has low mastery (via BKT
    state or assessment scores) receive higher scores.

    Returns 0-1 (1 = addresses the biggest knowledge gap).
    """
    try:
        assessment = player.assessment
    except Exception:
        return 0.5  # No assessment data -- neutral score

    # Identify the player's weakest trait among the challenge's targets
    target_traits = [challenge.primary_trait]
    if challenge.secondary_trait:
        target_traits.append(challenge.secondary_trait)

    weakest_mastery = 100.0
    for trait in target_traits:
        if hasattr(assessment, trait):
            mastery = getattr(assessment, trait, 50.0)
            weakest_mastery = min(weakest_mastery, mastery)

    # Normalise: low mastery -> high score (invert)
    return max(0.0, min(1.0, 1.0 - weakest_mastery / 100.0))


# ======================================================================
# Signal 3: Content-based filtering (personality alignment)
# ======================================================================
def content_based_score(assessment, challenge) -> float:
    """Cosine similarity between the player's personality profile and the
    challenge's trait fingerprint.

    Parameters
    ----------
    assessment : PersonalityAssessment
    challenge : Challenge

    Returns
    -------
    float
        0-1 similarity score.
    """
    player_vec = _assessment_trait_vector(assessment)
    challenge_vec = _challenge_trait_vector(challenge)
    # Cosine similarity is in [-1, 1]; shift to [0, 1]
    return (1.0 + _cosine_similarity(player_vec, challenge_vec)) / 2.0


# ======================================================================
# Signal 4: FSRS due cards
# ======================================================================
def _fsrs_score(player, challenge) -> float:
    """Check whether this challenge (or its skill) is due for review
    according to FSRS scheduling.

    Returns 1.0 if the card is overdue, 0.5 if due today, 0.0 if not
    yet due, and a linear interpolation in-between.
    """
    from apps.ai_engine.models import SpacedRepetitionCard

    now = timezone.now()
    try:
        card = SpacedRepetitionCard.objects.get(
            player=player,
            challenge=challenge,
        )
    except SpacedRepetitionCard.DoesNotExist:
        # Never reviewed -- treat as due
        return 0.8

    if card.due_date is None:
        return 0.8

    days_until_due = (card.due_date - now).total_seconds() / 86400.0
    if days_until_due <= 0:
        # Overdue: score ramps from 0.5 to 1.0 over 7 overdue days
        return min(1.0, 0.5 + abs(days_until_due) / 14.0)
    # Upcoming: score decays linearly to 0 over the next 14 days
    return max(0.0, 0.5 - days_until_due / 28.0)


# ======================================================================
# Signal 5: Thompson Sampling (multi-armed bandit)
# ======================================================================
def thompson_sampling(successes: int, failures: int) -> float:
    """Draw a sample from the Beta posterior.

    Uses a Beta(successes + 1, failures + 1) distribution.
    The prior is Beta(1, 1) -- uniform.

    Parameters
    ----------
    successes : int
        Number of times this arm was selected and led to engagement.
    failures : int
        Number of times this arm was selected but did not lead to engagement.

    Returns
    -------
    float
        A single sample from the posterior, in [0, 1].
    """
    alpha = max(1, successes + 1)
    beta_param = max(1, failures + 1)
    return random.betavariate(alpha, beta_param)


def _thompson_score(player, challenge) -> float:
    """Thompson Sampling score for a challenge based on historical engagement.

    Uses the challenge_type as the bandit arm.  Success is defined as the
    player scoring >= 70 on that challenge type.
    """
    from apps.progression.models import PlayerChallengeResult

    results = PlayerChallengeResult.objects.filter(
        player=player,
        challenge__challenge_type=challenge.challenge_type,
    ).values_list('score', flat=True)

    successes = sum(1 for s in results if s >= 70)
    failures = sum(1 for s in results if s < 70)

    return thompson_sampling(successes, failures)


# ======================================================================
# Signal 6: Random exploration
# ======================================================================
def _exploration_score() -> float:
    """Uniform random score to encourage exploration of unseen content."""
    return random.random()


# ======================================================================
# Collaborative filtering (personality-space kNN)
# ======================================================================
def collaborative_score(player, challenge) -> float:
    """Collaborative filtering via cosine similarity on personality vectors.

    Finds the top-K most similar players (by assessment traits) and checks
    whether they enjoyed this challenge (score >= 70).

    Parameters
    ----------
    player : Player
    challenge : Challenge

    Returns
    -------
    float
        0-1 score based on similar players' outcomes.
    """
    from apps.assessment.models import PersonalityAssessment
    from apps.progression.models import PlayerChallengeResult

    K = 20  # neighbourhood size

    try:
        player_assessment = player.assessment
    except Exception:
        return 0.5

    player_vec = _assessment_trait_vector(player_assessment)

    # Fetch all other assessments (in a production system this would be
    # pre-computed and cached; for now we limit to 500 most recent).
    other_assessments = (
        PersonalityAssessment.objects
        .exclude(player=player)
        .select_related('player')
        .order_by('-updated_at')[:500]
    )

    # Compute similarities
    similarities: List[Tuple[float, int]] = []
    for oa in other_assessments:
        other_vec = _assessment_trait_vector(oa)
        sim = _cosine_similarity(player_vec, other_vec)
        similarities.append((sim, oa.player_id))

    # Top-K neighbours
    similarities.sort(key=lambda x: x[0], reverse=True)
    neighbours = similarities[:K]

    if not neighbours:
        return 0.5

    # Weighted vote: did neighbours enjoy this challenge?
    weighted_sum = 0.0
    weight_total = 0.0
    neighbour_ids = [n_id for _, n_id in neighbours]
    sim_map = {n_id: sim for sim, n_id in neighbours}

    results = PlayerChallengeResult.objects.filter(
        player_id__in=neighbour_ids,
        challenge=challenge,
    ).values_list('player_id', 'score')

    for player_id, score in results:
        sim = sim_map.get(player_id, 0)
        weighted_sum += sim * (1.0 if score >= 70 else 0.0)
        weight_total += abs(sim)

    if weight_total == 0:
        return 0.5

    return max(0.0, min(1.0, weighted_sum / weight_total))


# ======================================================================
# Main entry point
# ======================================================================
def hybrid_recommend(player, n: int = 5, candidate_limit: int = 200) -> list:
    """Return the top-*n* recommended challenges for a player.

    Algorithm
    ---------
    1. Gather candidate challenges (active, not recently completed).
    2. Score each candidate on six signals.
    3. Compute weighted composite score.
    4. Return the top-*n* challenges sorted by composite score descending.

    Parameters
    ----------
    player : Player
    n : int
        Number of recommendations to return.
    candidate_limit : int
        Maximum number of candidates to evaluate (for performance).

    Returns
    -------
    list[dict]
        Each dict has ``challenge``, ``composite_score``, and per-signal
        breakdown.
    """
    from apps.progression.models import PlayerChallengeResult
    from apps.realms.models import Challenge

    # --- Determine player IRT ability ---
    try:
        from apps.ai_engine.models import PlayerAbility
        ability = PlayerAbility.objects.filter(player=player).order_by('-last_updated').first()
        player_ability = ability.theta if ability else 0.0
    except Exception:
        player_ability = 0.0  # default to average ability

    # --- Load player assessment (once) ---
    try:
        assessment = player.assessment
    except Exception:
        assessment = None

    # --- Candidate selection ---
    # Exclude challenges completed with a perfect score in the last 7 days
    # to avoid repetition, but allow retry of failed ones.
    from datetime import timedelta
    recent_perfect_ids = set(
        PlayerChallengeResult.objects.filter(
            player=player,
            score=100,
            played_at__gte=timezone.now() - timedelta(days=7),
        ).values_list('challenge_id', flat=True)
    )

    candidates = (
        Challenge.objects
        .filter(is_active=True)
        .exclude(id__in=recent_perfect_ids)
        .select_related('quest', 'quest__realm')
        .order_by('?')[:candidate_limit]
    )

    scored: List[dict] = []

    for challenge in candidates:
        signals = {}

        # 1. IRT optimal difficulty
        signals['irt'] = _irt_score(player_ability, challenge.difficulty)

        # 2. BKT knowledge gaps
        signals['bkt'] = _bkt_score(player, challenge)

        # 3. Content-based filtering
        if assessment is not None:
            signals['content'] = content_based_score(assessment, challenge)
        else:
            signals['content'] = 0.5

        # 4. FSRS due cards
        signals['fsrs'] = _fsrs_score(player, challenge)

        # 5. Thompson Sampling
        signals['thompson'] = _thompson_score(player, challenge)

        # 6. Exploration
        signals['exploration'] = _exploration_score()

        # --- Composite ---
        composite = sum(
            signals[key] * SIGNAL_WEIGHTS[key] for key in SIGNAL_WEIGHTS
        )

        scored.append({
            'challenge': challenge,
            'challenge_id': challenge.id,
            'composite_score': round(composite, 4),
            'signals': {k: round(v, 4) for k, v in signals.items()},
        })

    # Sort by composite score descending
    scored.sort(key=lambda x: x['composite_score'], reverse=True)

    return scored[:n]
