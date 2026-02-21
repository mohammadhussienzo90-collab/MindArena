"""
Bayesian Knowledge Tracing (BKT) Engine.

This module implements the standard Hidden Markov Model for tracking learner
knowledge on a per-skill basis. BKT is used by Carnegie Learning, ASSISTments,
and many intelligent tutoring systems worldwide.

Model overview
--------------
Each skill is modelled as a binary latent variable:
    K_t in {known, unknown}

The model has four parameters:

    P(L0) : Prior probability the skill is already known before any practice.
    P(T)  : Probability of transitioning from unknown -> known after one
             learning opportunity (the "learning rate").
    P(G)  : Probability of answering correctly despite NOT knowing the skill
             ("guessing").
    P(S)  : Probability of answering incorrectly despite knowing the skill
             ("slipping").

After each observation (correct / incorrect), Bayes' rule updates the
posterior P(K_t | observations):

    If correct:
        P(K_t | correct) = P(correct | known) * P(known)
                           / P(correct)
    If incorrect:
        P(K_t | incorrect) = P(incorrect | known) * P(known)
                             / P(incorrect)

Then the learning transition is applied:
    P(K_{t+1}) = P(K_t | obs) + (1 - P(K_t | obs)) * P(T)

A skill is considered "mastered" when P(K) >= 0.95.

References
----------
- Corbett, A. T. & Anderson, J. R. (1994). Knowledge Tracing: Modeling
  the Acquisition of Procedural Knowledge. User Modeling and User-Adapted
  Interaction, 4(4), 253-278.
- Pardos, Z. A. & Heffernan, N. T. (2010). Modeling Individualization
  in a Bayesian Networks Implementation of Knowledge Tracing.
"""

import math
from typing import Any, Dict, List, Optional, Tuple


class BKTEngine:
    """Bayesian Knowledge Tracing engine for per-skill mastery estimation.

    Default parameters
    ------------------
    P(L0) = 0.3  : 30% prior probability of already knowing a skill
    P(T)  = 0.1  : 10% chance of learning per opportunity
    P(G)  = 0.25 : 25% chance of guessing correctly (4-option MCQ baseline)
    P(S)  = 0.1  : 10% chance of slipping despite knowing

    These defaults are conservative and well-suited for initial deployment.
    Per-skill parameters can be learned from data using EM or grid search.
    """

    MASTERY_THRESHOLD = 0.95

    # ------------------------------------------------------------------
    # Core Bayesian update
    # ------------------------------------------------------------------

    @staticmethod
    def update(
        p_known: float,
        p_learn: float,
        p_guess: float,
        p_slip: float,
        is_correct: bool,
    ) -> float:
        """Update P(known) after observing a single response.

        Applies Bayes' rule to compute the posterior probability of knowing
        the skill given the observed response, then applies the learning
        transition.

        Parameters
        ----------
        p_known : float
            Prior P(known) before this observation.
        p_learn : float
            P(T) -- probability of learning per opportunity.
        p_guess : float
            P(G) -- probability of guessing correctly when unknown.
        p_slip : float
            P(S) -- probability of slipping when known.
        is_correct : bool
            Whether the player answered correctly.

        Returns
        -------
        float
            Updated P(known), clamped to [0.001, 0.999] to prevent
            numerical degeneracy.
        """
        if is_correct:
            # Bayes' rule: P(known | correct)
            p_correct_known = 1.0 - p_slip
            p_correct_unknown = p_guess
            p_correct = p_correct_known * p_known + p_correct_unknown * (1.0 - p_known)

            if p_correct < 1e-10:
                p_known_given_obs = p_known
            else:
                p_known_given_obs = (p_correct_known * p_known) / p_correct
        else:
            # Bayes' rule: P(known | incorrect)
            p_incorrect_known = p_slip
            p_incorrect_unknown = 1.0 - p_guess
            p_incorrect = (
                p_incorrect_known * p_known
                + p_incorrect_unknown * (1.0 - p_known)
            )

            if p_incorrect < 1e-10:
                p_known_given_obs = p_known
            else:
                p_known_given_obs = (p_incorrect_known * p_known) / p_incorrect

        # Learning transition: even if not known yet, there is a P(T) chance
        # the learner has now acquired the skill
        new_p_known = p_known_given_obs + (1.0 - p_known_given_obs) * p_learn

        return max(0.001, min(0.999, new_p_known))

    # ------------------------------------------------------------------
    # Mastery check
    # ------------------------------------------------------------------

    @classmethod
    def is_mastered(cls, p_known: float) -> bool:
        """Check whether a skill is mastered.

        A skill is considered mastered when the posterior probability of
        knowing it exceeds the mastery threshold (default 0.95).

        Parameters
        ----------
        p_known : float
            Current posterior P(known).

        Returns
        -------
        bool
            True if the skill is mastered.
        """
        return p_known >= cls.MASTERY_THRESHOLD

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    @staticmethod
    def expected_correct(
        p_known: float, p_guess: float, p_slip: float
    ) -> float:
        """Compute the expected probability of a correct answer.

        This is the marginal probability over the latent knowledge state:
            P(correct) = P(known) * (1 - P(slip)) + P(unknown) * P(guess)

        Useful for predicting performance and calibrating challenge difficulty.

        Parameters
        ----------
        p_known : float
            Current P(known).
        p_guess : float
            P(G) -- guessing probability.
        p_slip : float
            P(S) -- slipping probability.

        Returns
        -------
        float
            Expected probability of a correct response.
        """
        return p_known * (1.0 - p_slip) + (1.0 - p_known) * p_guess

    # ------------------------------------------------------------------
    # Batch update
    # ------------------------------------------------------------------

    @staticmethod
    def update_from_sequence(
        p_known: float,
        p_learn: float,
        p_guess: float,
        p_slip: float,
        responses: List[bool],
    ) -> Tuple[float, List[float]]:
        """Update P(known) from a sequence of responses.

        Applies ``update`` iteratively and returns the full trajectory,
        which is useful for visualization and analytics.

        Parameters
        ----------
        p_known : float
            Initial P(known).
        p_learn, p_guess, p_slip : float
            BKT parameters.
        responses : list of bool
            Sequence of correct/incorrect observations.

        Returns
        -------
        (final_p_known, trajectory) : tuple
            Final P(known) and the full list of intermediate P(known) values
            (one per response, including the final value).
        """
        trajectory = []
        for is_correct in responses:
            p_known = BKTEngine.update(p_known, p_learn, p_guess, p_slip, is_correct)
            trajectory.append(p_known)
        return p_known, trajectory

    # ------------------------------------------------------------------
    # Opportunities to mastery
    # ------------------------------------------------------------------

    @staticmethod
    def opportunities_to_mastery(
        p_known: float,
        p_learn: float,
        p_guess: float,
        p_slip: float,
        threshold: float = 0.95,
        max_steps: int = 200,
    ) -> Optional[int]:
        """Estimate the number of correct responses needed to reach mastery.

        Simulates the best-case (all correct) trajectory and counts how
        many opportunities are needed for P(known) to reach the threshold.

        Parameters
        ----------
        p_known : float
            Current P(known).
        p_learn, p_guess, p_slip : float
            BKT parameters.
        threshold : float, optional
            Mastery threshold (default 0.95).
        max_steps : int, optional
            Maximum simulation steps (default 200). Returns None if
            mastery is not reached.

        Returns
        -------
        int or None
            Number of correct responses needed, or None if unreachable
            within max_steps.
        """
        if p_known >= threshold:
            return 0

        for step in range(1, max_steps + 1):
            p_known = BKTEngine.update(p_known, p_learn, p_guess, p_slip, True)
            if p_known >= threshold:
                return step

        return None

    # ------------------------------------------------------------------
    # Django-integrated methods
    # ------------------------------------------------------------------

    @staticmethod
    def identify_gaps(player) -> List[Tuple[Any, float]]:
        """Find skills with the lowest P(known) for a given player.

        Queries the KnowledgeState model and returns skills ordered by
        ascending mastery, making it easy to identify knowledge gaps.

        Parameters
        ----------
        player : Player model instance
            The player whose knowledge gaps to identify.

        Returns
        -------
        list of (skill, p_known)
            Skills ordered from weakest to strongest.
        """
        from apps.ai_engine.models import KnowledgeState

        states = KnowledgeState.objects.filter(player=player).order_by("p_known")
        return [(s.skill, s.p_known) for s in states]

    @staticmethod
    def suggest_skill_focus(player, n: int = 3):
        """Suggest the top-N skills for the player to focus on.

        Strategy
        --------
        The selection mixes two types of skills:
        1. **Near-mastery skills** (P(known) in [0.3, 0.95)): These are
           motivating because the player is close to mastery. Up to n-1
           of these are selected, ordered by descending P(known) (closest
           to mastery first).
        2. **Weak skills** (P(known) < 0.3): These represent significant
           growth areas. At most 1 is included to avoid overwhelming the
           player.

        This mix ensures the player experiences both quick wins (motivating)
        and meaningful challenge (growth).

        Parameters
        ----------
        player : Player model instance
            The player to generate suggestions for.
        n : int, optional
            Total number of skills to suggest (default 3).

        Returns
        -------
        list of KnowledgeState instances
            Combined list of near-mastery and weak skill states.
        """
        from apps.ai_engine.models import KnowledgeState

        # Near-mastery: close to 0.95 but not yet there, with at least 1 observation
        near_mastery = list(
            KnowledgeState.objects.filter(
                player=player,
                p_known__lt=0.95,
                p_known__gte=0.3,
                observations__gt=0,
            ).order_by("-p_known")[: max(1, n - 1)]
        )

        # Weak: significant knowledge gaps
        weak = list(
            KnowledgeState.objects.filter(
                player=player,
                p_known__lt=0.3,
            ).order_by("p_known")[:1]
        )

        return near_mastery + weak

    @staticmethod
    def knowledge_summary(player) -> Dict[str, Dict[str, Any]]:
        """Generate a complete knowledge summary for the player dashboard.

        Returns a dictionary keyed by skill name, with each value containing
        the current mastery probability, mastery status, observation count,
        and skill category.

        Parameters
        ----------
        player : Player model instance
            The player whose knowledge to summarise.

        Returns
        -------
        dict
            Mapping of skill name -> {p_known, mastered, observations, category}.
        """
        from apps.ai_engine.models import KnowledgeState

        SKILL_CATEGORIES = {
            "analytical_thinking": "Cognitive",
            "creative_thinking": "Cognitive",
            "practical_thinking": "Cognitive",
            "openness": "Personality",
            "conscientiousness": "Personality",
            "extraversion": "Personality",
            "agreeableness": "Personality",
            "neuroticism": "Personality",
            "self_awareness": "Emotional",
            "empathy": "Emotional",
            "emotional_regulation": "Emotional",
            "social_skills": "Social",
            "risk_tolerance": "Decision",
        }

        states = KnowledgeState.objects.filter(player=player)
        summary = {}
        for s in states:
            summary[s.skill] = {
                "p_known": round(s.p_known, 3),
                "mastered": s.p_known >= 0.95,
                "observations": s.observations,
                "category": SKILL_CATEGORIES.get(s.skill, "Other"),
            }
        return summary
