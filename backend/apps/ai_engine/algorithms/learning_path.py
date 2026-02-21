"""
Learning Path Optimizer
========================
Skill prerequisite graph, topological sorting, personalised learning-path
generation, and weekly curriculum planning.

The skill graph encodes MindArena's 11 core psychological/cognitive skills
and their prerequisite relationships.  Paths are generated dynamically per
player, prioritising skills where the player has the most room to grow.
"""
from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import date, timedelta
from typing import Dict, List, Optional, Set

from django.utils import timezone

logger = logging.getLogger(__name__)

# ======================================================================
# Skill Prerequisite Graph
# ======================================================================
# Each key maps to a list of prerequisites that must be developed first.
SKILL_GRAPH: Dict[str, List[str]] = {
    # Foundations (no prerequisites)
    'self_awareness': [],
    'analytical_thinking': [],
    'conscientiousness': [],
    'openness': [],

    # Emotional intelligence branch
    'empathy': ['self_awareness'],
    'emotional_regulation': ['self_awareness'],
    'social_skills': ['empathy', 'emotional_regulation'],
    'agreeableness': ['empathy'],

    # Cognitive branch
    'creative_thinking': ['analytical_thinking'],
    'practical_thinking': ['analytical_thinking'],

    # Advanced (cross-branch)
    'risk_tolerance': ['analytical_thinking', 'emotional_regulation'],
}

# Reverse map: skill -> list of skills that depend on it
_DEPENDENTS: Dict[str, List[str]] = defaultdict(list)
for _skill, _prereqs in SKILL_GRAPH.items():
    for _prereq in _prereqs:
        _DEPENDENTS[_prereq].append(_skill)


# ======================================================================
# Graph utilities
# ======================================================================
def topological_sort(graph: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Kahn's algorithm for topological sorting of the skill graph.

    Parameters
    ----------
    graph : dict, optional
        Adjacency list mapping skill -> prerequisites.
        Defaults to ``SKILL_GRAPH``.

    Returns
    -------
    list[str]
        Skills in a valid learning order (prerequisites before dependants).

    Raises
    ------
    ValueError
        If the graph contains a cycle.
    """
    if graph is None:
        graph = SKILL_GRAPH

    # Build in-degree map
    in_degree: Dict[str, int] = {skill: 0 for skill in graph}
    adjacency: Dict[str, List[str]] = defaultdict(list)  # prereq -> [dependants]

    for skill, prereqs in graph.items():
        in_degree.setdefault(skill, 0)
        for prereq in prereqs:
            in_degree.setdefault(prereq, 0)
            adjacency[prereq].append(skill)
            in_degree[skill] += 1

    # Start with nodes that have no prerequisites
    queue: deque = deque(
        skill for skill, deg in in_degree.items() if deg == 0
    )
    result: List[str] = []

    while queue:
        skill = queue.popleft()
        result.append(skill)
        for dependant in adjacency[skill]:
            in_degree[dependant] -= 1
            if in_degree[dependant] == 0:
                queue.append(dependant)

    if len(result) != len(in_degree):
        visited = set(result)
        cycle_members = [s for s in in_degree if s not in visited]
        raise ValueError(
            f"Cycle detected in skill graph involving: {cycle_members}"
        )

    return result


def get_prerequisites(skill: str) -> Set[str]:
    """Return the transitive closure of all prerequisites for a skill.

    Parameters
    ----------
    skill : str
        Target skill name.

    Returns
    -------
    set[str]
        All direct and indirect prerequisites.
    """
    visited: Set[str] = set()
    stack = list(SKILL_GRAPH.get(skill, []))

    while stack:
        current = stack.pop()
        if current not in visited:
            visited.add(current)
            stack.extend(SKILL_GRAPH.get(current, []))

    return visited


def get_dependants(skill: str) -> Set[str]:
    """Return all skills that transitively depend on the given skill."""
    visited: Set[str] = set()
    stack = list(_DEPENDENTS.get(skill, []))

    while stack:
        current = stack.pop()
        if current not in visited:
            visited.add(current)
            stack.extend(_DEPENDENTS.get(current, []))

    return visited


# ======================================================================
# Mastery assessment
# ======================================================================
def _get_skill_mastery(player) -> Dict[str, float]:
    """Compute the player's current mastery (0-100) for each skill.

    Uses the PersonalityAssessment trait scores as the primary source,
    falling back to 50 (neutral) if no assessment exists.
    """
    mastery: Dict[str, float] = {}

    try:
        assessment = player.assessment
        for skill in SKILL_GRAPH:
            mastery[skill] = getattr(assessment, skill, 50.0)
    except Exception:
        for skill in SKILL_GRAPH:
            mastery[skill] = 50.0

    return mastery


def _prerequisites_satisfied(
    skill: str,
    mastered: Set[str],
    threshold: float = 40.0,
    mastery: Optional[Dict[str, float]] = None,
) -> bool:
    """Check whether all prerequisites of *skill* meet the mastery threshold."""
    for prereq in SKILL_GRAPH.get(skill, []):
        if prereq not in mastered:
            if mastery and mastery.get(prereq, 0) < threshold:
                return False
            elif not mastery:
                return False
    return True


# ======================================================================
# Learning path generation
# ======================================================================
def generate_learning_path(
    player,
    mastery_threshold: float = 70.0,
    max_skills: int = 11,
) -> List[Dict[str, object]]:
    """Generate a personalised learning path respecting prerequisites.

    Algorithm
    ---------
    1. Compute current mastery for each skill.
    2. Identify skills below the mastery threshold.
    3. Topologically sort the unmastered skills.
    4. Prioritise skills with the lowest mastery that have satisfied prereqs.

    Parameters
    ----------
    player : Player
    mastery_threshold : float
        Skills at or above this level are considered mastered.
    max_skills : int
        Maximum number of skills to include in the path.

    Returns
    -------
    list[dict]
        Ordered list of skill dicts with ``skill``, ``current_mastery``,
        ``target_mastery``, ``priority``, ``prerequisites``, ``dependants``.
    """
    mastery = _get_skill_mastery(player)
    topo_order = topological_sort()

    # Skills that still need work
    unmastered = [
        s for s in topo_order if mastery.get(s, 0) < mastery_threshold
    ]

    if not unmastered:
        logger.info("Player %s has mastered all skills", player)
        return []

    # Build the path: maintain topological order but prioritise low mastery
    mastered_set: Set[str] = {
        s for s, m in mastery.items() if m >= mastery_threshold
    }

    # Two-pass: first emit skills whose prereqs are already mastered,
    # sorted by ascending mastery (weakest first).
    ready: List[str] = []
    deferred: List[str] = []

    for skill in unmastered:
        if _prerequisites_satisfied(skill, mastered_set, mastery_threshold, mastery):
            ready.append(skill)
        else:
            deferred.append(skill)

    # Sort ready skills by current mastery (weakest first = highest priority)
    ready.sort(key=lambda s: mastery.get(s, 0))

    # Now interleave deferred skills: once a ready skill is "completed"
    # (added to path), its dependants may become ready.
    path: List[str] = []
    path_set: Set[str] = set(mastered_set)

    while (ready or deferred) and len(path) < max_skills:
        if ready:
            skill = ready.pop(0)
            path.append(skill)
            path_set.add(skill)

            # Check if any deferred skills are now unblocked
            still_deferred: List[str] = []
            for d in deferred:
                if _prerequisites_satisfied(d, path_set, mastery_threshold, mastery):
                    ready.append(d)
                else:
                    still_deferred.append(d)
            deferred = still_deferred
            # Re-sort ready by mastery
            ready.sort(key=lambda s: mastery.get(s, 0))
        elif deferred:
            # Force-add the first deferred skill (prereqs will be implicit)
            skill = deferred.pop(0)
            path.append(skill)
            path_set.add(skill)

    # Build output
    result: List[Dict[str, object]] = []
    for idx, skill in enumerate(path):
        result.append({
            'skill': skill,
            'current_mastery': round(mastery.get(skill, 0), 1),
            'target_mastery': mastery_threshold,
            'priority': idx + 1,
            'prerequisites': SKILL_GRAPH.get(skill, []),
            'dependants': list(get_dependants(skill) & set(path)),
        })

    return result


# ======================================================================
# Weekly plan generation
# ======================================================================
def generate_weekly_plan(
    player,
    challenges_per_day: int = 3,
    plan_days: int = 7,
) -> List[Dict[str, object]]:
    """Generate a 7-day learning plan with daily challenge assignments.

    Algorithm
    ---------
    1. Generate the learning path.
    2. For each day, select challenges that target the current focus skill.
    3. Rotate skills once enough challenges are completed (or daily quota met).
    4. Include one "review" challenge per day from a previously studied skill.

    Parameters
    ----------
    player : Player
    challenges_per_day : int
        Number of challenges per day.
    plan_days : int
        Number of days to plan (default: 7).

    Returns
    -------
    list[dict]
        One entry per day with ``day`` (1-7), ``date``, ``focus_skill``,
        ``challenges`` (list of challenge dicts), ``review_skill``.
    """
    from apps.progression.models import PlayerChallengeResult
    from apps.realms.models import Challenge

    learning_path = generate_learning_path(player)
    mastery = _get_skill_mastery(player)

    if not learning_path:
        # Player has mastered everything -- provide review-only plan
        learning_path = [
            {'skill': s, 'current_mastery': mastery.get(s, 0)}
            for s in topological_sort()
        ]

    today = date.today()
    plan: List[Dict[str, object]] = []

    # Track which challenges we have already assigned to avoid repeats
    assigned_challenge_ids: Set[int] = set()

    # Distribute skills across the week
    skill_queue = [entry['skill'] for entry in learning_path]
    if not skill_queue:
        skill_queue = list(SKILL_GRAPH.keys())

    # Challenges the player has recently completed (for review selection)
    recent_results = (
        PlayerChallengeResult.objects
        .filter(player=player)
        .order_by('-played_at')
        .values_list('challenge_id', 'challenge__primary_trait')[:100]
    )
    reviewed_skills = list({trait for _, trait in recent_results if trait})

    for day_num in range(1, plan_days + 1):
        day_date = today + timedelta(days=day_num - 1)

        # Pick focus skill (rotate through the learning path)
        focus_idx = (day_num - 1) % len(skill_queue)
        focus_skill = skill_queue[focus_idx]

        # Pick review skill (a different, previously studied skill)
        review_skill = None
        if reviewed_skills:
            # Choose a review skill different from today's focus
            for rs in reviewed_skills:
                if rs != focus_skill:
                    review_skill = rs
                    break
            if review_skill is None and reviewed_skills:
                review_skill = reviewed_skills[0]

        # Select challenges for the day
        new_challenges_needed = challenges_per_day
        if review_skill:
            new_challenges_needed = max(1, challenges_per_day - 1)

        # Fetch new challenges targeting the focus skill
        focus_challenges = list(
            Challenge.objects
            .filter(
                is_active=True,
                primary_trait=focus_skill,
            )
            .exclude(id__in=assigned_challenge_ids)
            .order_by('difficulty', '?')[:new_challenges_needed]
        )

        # If not enough, broaden to secondary trait
        if len(focus_challenges) < new_challenges_needed:
            extra_needed = new_challenges_needed - len(focus_challenges)
            extra = list(
                Challenge.objects
                .filter(
                    is_active=True,
                    secondary_trait=focus_skill,
                )
                .exclude(id__in=assigned_challenge_ids)
                .exclude(id__in=[c.id for c in focus_challenges])
                .order_by('difficulty', '?')[:extra_needed]
            )
            focus_challenges.extend(extra)

        # If still not enough, pick any available challenge
        if len(focus_challenges) < new_challenges_needed:
            extra_needed = new_challenges_needed - len(focus_challenges)
            extra = list(
                Challenge.objects
                .filter(is_active=True)
                .exclude(id__in=assigned_challenge_ids)
                .exclude(id__in=[c.id for c in focus_challenges])
                .order_by('?')[:extra_needed]
            )
            focus_challenges.extend(extra)

        # Fetch one review challenge
        review_challenges: list = []
        if review_skill:
            review_qs = (
                Challenge.objects
                .filter(
                    is_active=True,
                    primary_trait=review_skill,
                )
                .exclude(id__in=assigned_challenge_ids)
                .exclude(id__in=[c.id for c in focus_challenges])
                .order_by('?')[:1]
            )
            review_challenges = list(review_qs)

        day_challenges = focus_challenges + review_challenges
        assigned_challenge_ids.update(c.id for c in day_challenges)

        plan.append({
            'day': day_num,
            'date': day_date.isoformat(),
            'focus_skill': focus_skill,
            'focus_mastery': round(mastery.get(focus_skill, 50.0), 1),
            'review_skill': review_skill,
            'challenges': [
                {
                    'challenge_id': c.id,
                    'title': c.title_en,
                    'difficulty': c.difficulty,
                    'type': c.challenge_type,
                    'primary_trait': c.primary_trait,
                    'is_review': c.primary_trait == review_skill,
                }
                for c in day_challenges
            ],
            'challenge_count': len(day_challenges),
        })

    return plan


# ======================================================================
# Utility: skill readiness check
# ======================================================================
def skill_readiness(player, skill: str) -> Dict[str, object]:
    """Check whether a player is ready to study a specific skill.

    Returns
    -------
    dict
        ``ready`` (bool), ``missing_prerequisites`` (list),
        ``current_mastery``, ``recommended_order``.
    """
    mastery = _get_skill_mastery(player)
    prereqs = SKILL_GRAPH.get(skill, [])

    missing = [
        {
            'skill': p,
            'current_mastery': round(mastery.get(p, 0), 1),
            'needed': 40.0,
        }
        for p in prereqs
        if mastery.get(p, 0) < 40.0
    ]

    # Recommended study order to unlock this skill
    all_prereqs = get_prerequisites(skill)
    unmet = [
        p for p in topological_sort()
        if p in all_prereqs and mastery.get(p, 0) < 40.0
    ]

    return {
        'skill': skill,
        'ready': len(missing) == 0,
        'current_mastery': round(mastery.get(skill, 0), 1),
        'missing_prerequisites': missing,
        'recommended_order': unmet + [skill],
    }
