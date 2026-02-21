"""
Free Spaced Repetition Scheduler v4.5 (FSRS-4.5) Engine.

This module implements the FSRS algorithm as used in Anki 23+ for
scientifically optimal spaced repetition scheduling.

FSRS models two latent variables per memory:
    - **Stability (S)**: The number of days at which retrievability = 90%.
      Higher stability means the memory decays more slowly.
    - **Difficulty (D)**: How inherently hard the material is to retain,
      on a 1-10 scale.

After each review, FSRS updates S and D based on the rating and the
elapsed time, then computes the optimal interval to the next review.

The retrievability (probability of recall) follows a power-law forgetting
curve:
    R(t) = (1 + FACTOR * t / S) ^ DECAY

where FACTOR = 19/81 and DECAY = -0.5, calibrated so that R(S) = 0.9
(i.e., at t = S days, the probability of recall is exactly 90%).

References
----------
- Ye, J. (2023). A Stochastic Shortest Path Algorithm for Optimizing
  Spaced Repetition Scheduling. https://arxiv.org/abs/2402.01624
- https://github.com/open-spaced-repetition/fsrs4anki
- Anki 23.10+ built-in FSRS implementation.

Parameters
----------
The 17 default weights (W[0]..W[16]) are the FSRS-4.5 optimizer defaults
trained on millions of Anki reviews. They can be personalised per-user
by running the FSRS optimizer on the user's review history.
"""

import math
from datetime import timedelta
from typing import Any, Dict, Optional

from django.utils import timezone


class FSRSEngine:
    """FSRS-4.5 algorithm -- state-of-the-art spaced repetition scheduler.

    All methods are classmethods so they can be called without instantiation
    while still allowing subclasses to override the weight vector W.

    Card states
    -----------
    0 : New        -- never reviewed
    1 : Learning   -- first exposure, short intervals
    2 : Review     -- graduated to long-term schedule
    3 : Relearning -- lapsed; short intervals again until re-stabilised
    """

    # FSRS-4.5 default weight vector (from the Anki FSRS optimizer).
    # W[0..3]  : initial stability for ratings 1-4
    # W[4]     : initial difficulty mean
    # W[5]     : initial difficulty slope
    # W[6]     : difficulty update weight
    # W[7]     : difficulty mean-reversion factor
    # W[8..10] : recall stability modifiers
    # W[11..14]: forget stability modifiers
    # W[15]    : hard penalty multiplier
    # W[16]    : easy bonus multiplier
    W = [
        0.4, 0.6, 2.4, 5.8,   # W[0]-W[3]: init stability per rating
        4.93,                    # W[4]: init difficulty intercept
        0.94,                    # W[5]: init difficulty slope
        0.86,                    # W[6]: difficulty update rate
        0.01,                    # W[7]: difficulty mean-reversion
        1.49,                    # W[8]: recall stability growth
        0.14,                    # W[9]: recall stability decay
        0.94,                    # W[10]: recall retrievability weight
        2.18,                    # W[11]: forget stability base
        0.05,                    # W[12]: forget difficulty penalty
        0.34,                    # W[13]: forget stability growth
        1.26,                    # W[14]: forget retrievability weight
        0.29,                    # W[15]: hard penalty
        2.61,                    # W[16]: easy bonus
    ]

    # Power-law forgetting curve parameters.
    # Chosen so that R(S) = 0.9, i.e. at t = S days retrievability is 90%.
    DECAY = -0.5
    FACTOR = 19.0 / 81.0  # = 0.9^(1/DECAY) - 1

    # ------------------------------------------------------------------
    # Initial state for new cards
    # ------------------------------------------------------------------

    @classmethod
    def init_stability(cls, rating: int) -> float:
        """Compute initial stability for a new card.

        Parameters
        ----------
        rating : int
            First review rating (1 = Again, 2 = Hard, 3 = Good, 4 = Easy).

        Returns
        -------
        float
            Initial stability in days.
        """
        return max(0.1, cls.W[rating - 1])

    @classmethod
    def init_difficulty(cls, rating: int) -> float:
        """Compute initial difficulty for a new card.

        Uses a decreasing exponential: higher first-rating -> lower difficulty.

        Parameters
        ----------
        rating : int
            First review rating (1-4).

        Returns
        -------
        float
            Initial difficulty, clamped to [1, 10].
        """
        return min(10.0, max(1.0, cls.W[4] - math.exp(cls.W[5] * (rating - 1)) + 1))

    # ------------------------------------------------------------------
    # State transition functions
    # ------------------------------------------------------------------

    @classmethod
    def next_difficulty(cls, d: float, rating: int) -> float:
        """Update difficulty after a review.

        Applies a mean-reversion mechanism (controlled by W[7]) that pulls
        difficulty toward the population mean, preventing extreme drift.

        Parameters
        ----------
        d : float
            Current difficulty (1-10).
        rating : int
            Review rating (1-4). Rating 3 is neutral (no change before
            mean-reversion).

        Returns
        -------
        float
            Updated difficulty, clamped to [1, 10].
        """
        new_d = d - cls.W[6] * (rating - 3)
        # Mean-reversion toward the difficulty of a "Good" first review
        new_d = cls.W[7] * cls.init_difficulty(3) + (1.0 - cls.W[7]) * new_d
        return min(10.0, max(1.0, new_d))

    @classmethod
    def next_recall_stability(
        cls, d: float, s: float, r: float, rating: int
    ) -> float:
        """Compute new stability after a successful recall (rating >= 2).

        The stability increase factor (SInc) is:
            SInc = 1 + exp(W[8]) * (11 - D) * S^(-W[9])
                     * (exp((1 - R) * W[10]) - 1) * penalty * bonus

        Key properties:
        - Higher current stability -> smaller relative increase (diminishing
          returns).
        - Lower retrievability at review time -> bigger boost (desirable
          difficulty effect).
        - Hard reviews penalised, easy reviews boosted.

        Parameters
        ----------
        d : float
            Current difficulty (1-10).
        s : float
            Current stability in days.
        r : float
            Retrievability at the moment of review.
        rating : int
            Review rating (2 = Hard, 3 = Good, 4 = Easy).

        Returns
        -------
        float
            New stability in days (minimum 0.1).
        """
        hard_penalty = cls.W[15] if rating == 2 else 1.0
        easy_bonus = cls.W[16] if rating == 4 else 1.0

        new_s = s * (
            1.0
            + math.exp(cls.W[8])
            * (11.0 - d)
            * math.pow(s, -cls.W[9])
            * (math.exp((1.0 - r) * cls.W[10]) - 1.0)
            * hard_penalty
            * easy_bonus
        )
        return max(0.1, new_s)

    @classmethod
    def next_forget_stability(cls, d: float, s: float, r: float) -> float:
        """Compute new stability after a lapse (rating = 1, Again).

        When the learner forgets, stability is reset to a lower value.
        The new stability is always <= the old stability.

        Parameters
        ----------
        d : float
            Current difficulty (1-10).
        s : float
            Current stability in days.
        r : float
            Retrievability at the moment of review.

        Returns
        -------
        float
            New (reduced) stability in days, clamped to [0.1, old_s].
        """
        new_s = (
            cls.W[11]
            * math.pow(d, -cls.W[12])
            * (math.pow(s + 1.0, cls.W[13]) - 1.0)
            * math.exp((1.0 - r) * cls.W[14])
        )
        return max(0.1, min(new_s, s))

    # ------------------------------------------------------------------
    # Forgetting curve and scheduling
    # ------------------------------------------------------------------

    @classmethod
    def retrievability(cls, elapsed_days: float, stability: float) -> float:
        """Compute current probability of recall (retrievability).

        Uses the power-law forgetting curve:
            R(t) = (1 + FACTOR * t / S) ^ DECAY

        This provides a better empirical fit than the classic Ebbinghaus
        exponential decay, especially for longer retention intervals.

        Parameters
        ----------
        elapsed_days : float
            Days since last review.
        stability : float
            Current memory stability in days.

        Returns
        -------
        float
            Probability of recall, in [0, 1].
        """
        if stability <= 0:
            return 0.0
        return math.pow(1.0 + cls.FACTOR * elapsed_days / stability, cls.DECAY)

    @classmethod
    def next_interval(cls, stability: float, desired_retention: float = 0.9) -> int:
        """Calculate the optimal next review interval.

        Solves for t in R(t) = desired_retention:
            t = S / FACTOR * (desired_retention^(1/DECAY) - 1)

        Parameters
        ----------
        stability : float
            Current memory stability in days.
        desired_retention : float, optional
            Target retrievability at the next scheduled review (default 0.9,
            i.e. 90% chance of recall).

        Returns
        -------
        int
            Interval in days, clamped to [1, 365].
        """
        interval = (
            stability
            / cls.FACTOR
            * (math.pow(desired_retention, 1.0 / cls.DECAY) - 1.0)
        )
        return max(1, min(365, round(interval)))

    # ------------------------------------------------------------------
    # Main review processing
    # ------------------------------------------------------------------

    @classmethod
    def review_card(
        cls, card_state: Dict[str, Any], rating: int
    ) -> Dict[str, Any]:
        """Process a single review and return the updated card state.

        This is the main entry point for the scheduling loop. It handles
        all four card states (New, Learning, Review, Relearning) and
        transitions between them.

        Parameters
        ----------
        card_state : dict
            Current card state with keys:
            - state (int): 0=New, 1=Learning, 2=Review, 3=Relearning
            - stability (float): current S
            - difficulty_fsrs (float): current D
            - elapsed_days (int): days since last review
            - reps (int): total review count
            - lapses (int): total lapse (Again) count

        rating : int
            Review rating:
            1 = Again (forgot / incorrect)
            2 = Hard  (recalled with significant difficulty)
            3 = Good  (recalled with acceptable effort)
            4 = Easy  (recalled effortlessly)

        Returns
        -------
        dict
            Updated card state with all scheduling fields.
        """
        now = timezone.now()
        state = card_state.get("state", 0)

        if state == 0:
            # ---- New card: first review ever ----
            s = cls.init_stability(rating)
            d = cls.init_difficulty(rating)
            reps = 1
            lapses = card_state.get("lapses", 0)
        else:
            # ---- Existing card: update based on performance ----
            elapsed = card_state.get("elapsed_days", 0)
            old_s = card_state.get("stability", 1.0)
            old_d = card_state.get("difficulty_fsrs", 5.0)

            # Current retrievability at the moment of review
            r = cls.retrievability(elapsed, old_s)

            # Update difficulty
            d = cls.next_difficulty(old_d, rating)

            # Update stability
            if rating == 1:
                # Lapse: memory failed
                s = cls.next_forget_stability(d, old_s, r)
                lapses = card_state.get("lapses", 0) + 1
            else:
                # Successful recall
                s = cls.next_recall_stability(d, old_s, r, rating)
                lapses = card_state.get("lapses", 0)

            reps = card_state.get("reps", 0) + 1

        # Compute the optimal interval
        interval = cls.next_interval(s)

        # Determine the new card state
        if rating == 1:
            # Failed: go to Relearning (or Learning if first exposure)
            new_state = 3 if reps > 1 else 1
        else:
            # Passed: graduate to Review
            new_state = 2

        return {
            "stability": round(s, 4),
            "difficulty_fsrs": round(d, 4),
            "scheduled_days": interval,
            "elapsed_days": 0,
            "state": new_state,
            "due_date": now + timedelta(days=interval),
            "last_review": now,
            "reps": reps,
            "lapses": lapses,
        }

    # ------------------------------------------------------------------
    # Utility: convert challenge results to FSRS ratings
    # ------------------------------------------------------------------

    @classmethod
    def rating_from_result(
        cls,
        score: float,
        time_taken: float,
        time_limit: Optional[float],
    ) -> int:
        """Convert a MindArena challenge result into an FSRS rating (1-4).

        Mapping rules:
        - score < 50        -> 1 (Again): clear failure
        - 50 <= score < 70  -> 2 (Hard):  marginal pass
        - 70 <= score < 90  -> 3 (Good):  solid pass
        - score >= 90 AND completed in < 50% of time limit -> 4 (Easy)
        - score >= 90 otherwise -> 3 (Good)

        Parameters
        ----------
        score : float
            Challenge score as a percentage (0-100).
        time_taken : float
            Time the player spent on the challenge (seconds).
        time_limit : float or None
            Maximum allowed time for the challenge (seconds), or None
            if there is no time limit.

        Returns
        -------
        int
            FSRS rating: 1 (Again), 2 (Hard), 3 (Good), or 4 (Easy).
        """
        if score < 50:
            return 1  # Again
        if score < 70:
            return 2  # Hard
        if score >= 90 and time_limit and time_taken < time_limit * 0.5:
            return 4  # Easy
        return 3  # Good
