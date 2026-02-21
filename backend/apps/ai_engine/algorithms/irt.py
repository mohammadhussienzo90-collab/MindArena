"""
2-Parameter / 3-Parameter Logistic Item Response Theory (IRT) Engine.

This module implements the gold-standard psychometric model used by major
adaptive testing platforms (GRE, Duolingo, Khan Academy) to:

1. Estimate a player's latent ability (theta) from observed responses.
2. Select optimally informative challenges (maximum Fisher information).
3. Calibrate item parameters from historical response data.

Mathematical foundation
-----------------------
The 3PL IRT model defines the probability that a player with ability theta
answers an item correctly as:

    P(X=1 | theta, a, b, c) = c + (1 - c) / (1 + exp(-a * (theta - b)))

where:
    theta : latent ability on a logit scale, typically in [-4, +4]
    a     : item discrimination (slope), typically in [0.2, 3.0]
    b     : item difficulty (location), on the same scale as theta
    c     : pseudo-guessing parameter, e.g. 0.25 for 4-option MCQ

References
----------
- Lord, F. M. (1980). Applications of Item Response Theory to Practical
  Testing Problems. Lawrence Erlbaum Associates.
- Baker, F. B. & Kim, S.-H. (2004). Item Response Theory: Parameter
  Estimation Techniques. CRC Press.
"""

import math
from typing import List, Optional, Tuple


class IRTEngine:
    """2-Parameter / 3-Parameter Logistic Item Response Theory engine.

    All methods are stateless class/static methods so the engine can be used
    without instantiation, making it easy to call from Django views or Celery
    tasks without any shared mutable state.
    """

    # ------------------------------------------------------------------
    # Core IRT computations
    # ------------------------------------------------------------------

    @staticmethod
    def probability(theta: float, a: float, b: float, c: float = 0.25) -> float:
        """Compute P(correct) using the 3PL IRT model.

        Parameters
        ----------
        theta : float
            Player ability on the logit scale, typically in [-4, +4].
        a : float
            Item discrimination parameter, typically in [0.2, 3.0].
            Higher values mean the item differentiates sharply between
            players just above and just below the difficulty level.
        b : float
            Item difficulty parameter, on the same scale as theta.
        c : float, optional
            Pseudo-guessing (lower asymptote) parameter. For a standard
            4-option multiple-choice question the default is 0.25.

        Returns
        -------
        float
            Probability of a correct response, in (c, 1.0).
        """
        exponent = -a * (theta - b)
        # Clamp to prevent math.exp overflow (exp(710) overflows float64)
        exponent = max(-10.0, min(10.0, exponent))
        return c + (1.0 - c) / (1.0 + math.exp(exponent))

    @staticmethod
    def fisher_information(theta: float, a: float, b: float, c: float = 0.25) -> float:
        """Compute Fisher information of an item at a given ability level.

        Fisher information quantifies how much statistical information the
        item carries about the ability parameter theta. It is used for:
        - Optimal item selection (pick the item with max information).
        - Computing the standard error of theta: SE = 1 / sqrt(sum(I)).

        The 3PL Fisher information formula is:
            I(theta) = a^2 * (P* )^2 * Q / P

        where P* = (P - c) / (1 - c) and Q = 1 - P.

        Parameters
        ----------
        theta : float
            Current ability estimate.
        a, b, c : float
            Item parameters (see ``probability``).

        Returns
        -------
        float
            Fisher information (non-negative).
        """
        p = IRTEngine.probability(theta, a, b, c)
        q = 1.0 - p

        # P* is the "effective" probability without guessing
        if (1.0 - c) > 1e-12:
            p_star = (p - c) / (1.0 - c)
        else:
            p_star = p

        if p < 1e-10 or q < 1e-10:
            return 0.0

        return a ** 2 * p_star ** 2 * q / p

    # ------------------------------------------------------------------
    # Ability estimation via Newton-Raphson MLE
    # ------------------------------------------------------------------

    @staticmethod
    def update_theta(
        theta: float,
        theta_se: float,
        responses: List[Tuple[float, float, float, bool]],
        max_iterations: int = 10,
    ) -> Tuple[float, float]:
        """Update the ability estimate using Newton-Raphson MLE.

        Given the player's current theta and a batch of new responses, this
        method iteratively maximises the log-likelihood of the responses with
        respect to theta.

        The log-likelihood is:
            L(theta) = sum[ x_i * ln P_i + (1 - x_i) * ln(1 - P_i) ]

        The first derivative (score function) and second derivative (observed
        information) are used in the Newton-Raphson update:
            theta_{t+1} = theta_t + L'(theta_t) / (-L''(theta_t))

        Parameters
        ----------
        theta : float
            Current ability estimate.
        theta_se : float
            Current standard error of theta (used as a reference; a new SE
            is computed from the observed information).
        responses : list of (a, b, c, is_correct) tuples
            Each tuple contains the item parameters and whether the player
            answered correctly.
        max_iterations : int, optional
            Maximum Newton-Raphson iterations (default 10). Convergence is
            typically achieved in 3-5 iterations.

        Returns
        -------
        (new_theta, new_se) : tuple of float
            Updated ability estimate and its standard error.
        """
        denominator = 0.0  # Track across iterations for final SE

        for _ in range(max_iterations):
            numerator = 0.0
            denominator = 0.0

            for a, b, c, correct in responses:
                p = IRTEngine.probability(theta, a, b, c)

                # P* = (P - c) / (1 - c), the 2PL-equivalent probability
                if (1.0 - c) > 1e-12:
                    p_star = (p - c) / (1.0 - c)
                else:
                    p_star = p

                q = 1.0 - p

                # Score function contribution
                if correct:
                    if p > 1e-10:
                        numerator += a * (1.0 - p) * p_star / p
                else:
                    numerator -= a * p_star

                # Observed information contribution
                denominator += a ** 2 * p_star ** 2 * q / max(p, 1e-10)

            if abs(denominator) < 1e-10:
                break

            # Newton-Raphson step
            theta += numerator / denominator
            # Clamp theta to reasonable bounds
            theta = max(-4.0, min(4.0, theta))

        # Standard error from observed information
        new_se = 1.0 / math.sqrt(max(denominator, 0.01))
        return theta, min(new_se, 2.0)

    # ------------------------------------------------------------------
    # Optimal challenge selection
    # ------------------------------------------------------------------

    @staticmethod
    def select_optimal_challenge(
        theta: float,
        challenges_with_params: List[Tuple[int, float, float, float]],
        target_p: float = 0.75,
    ) -> List[Tuple[int, float, float, float]]:
        """Select the challenge closest to the target success probability.

        This implements the Zone of Proximal Development (ZPD) strategy:
        challenges are ranked by how close their expected success probability
        is to a pedagogically optimal target (default 0.75).

        A target of 0.75 balances:
        - Enough difficulty to promote learning (not trivially easy).
        - Enough success to maintain motivation and flow.
        - Maximum information gain about the player's ability.

        Parameters
        ----------
        theta : float
            Current ability estimate.
        challenges_with_params : list of (challenge_id, a, b, c)
            Available challenges with their IRT parameters.
        target_p : float, optional
            Target success probability (default 0.75).

        Returns
        -------
        list of (challenge_id, expected_p, fisher_info, distance)
            Sorted by ascending distance from the target probability.
        """
        candidates = []
        for challenge_id, a, b, c in challenges_with_params:
            p = IRTEngine.probability(theta, a, b, c)
            info = IRTEngine.fisher_information(theta, a, b, c)
            distance = abs(p - target_p)
            candidates.append((challenge_id, p, info, distance))

        # Sort by distance to target probability (primary), then by
        # descending Fisher information (secondary tie-breaker)
        candidates.sort(key=lambda x: (x[3], -x[2]))
        return candidates

    # ------------------------------------------------------------------
    # Parameter initialization and calibration
    # ------------------------------------------------------------------

    @staticmethod
    def initialize_from_difficulty(difficulty_1_10: float) -> float:
        """Convert a human-readable difficulty rating (1-10) to the IRT b parameter.

        Uses a linear mapping:
            difficulty 1  -> b = -2.0
            difficulty 10 -> b = +2.0
            difficulty 5.5 -> b = 0.0  (average)

        Parameters
        ----------
        difficulty_1_10 : float
            Difficulty rating on a 1-10 scale (as set by content creators).

        Returns
        -------
        float
            IRT difficulty parameter b.
        """
        return (difficulty_1_10 - 5.5) * (4.0 / 9.0)

    @staticmethod
    def calibrate_from_data(
        responses: List[Tuple[float, bool]],
    ) -> Optional[Tuple[float, float]]:
        """Re-calibrate item parameters (a, b) from historical response data.

        Uses a simple closed-form approximation based on the difference in
        mean ability between correct and incorrect responders:

        - b is estimated as the midpoint of the two group means.
        - a is estimated from the inverse of the spread (sharper separation
          implies higher discrimination).

        This is a fast heuristic suitable for online recalibration. For
        full precision, use joint MLE / MCMC on the complete response matrix.

        Parameters
        ----------
        responses : list of (theta, is_correct)
            Historical responses with the responding player's ability
            estimate at the time of response.

        Returns
        -------
        (a, b) : tuple of float, or None
            Estimated discrimination and difficulty. Returns None if there
            are fewer than 10 responses or if all responses are the same.
        """
        if len(responses) < 10:
            return None

        correct = [(t, c) for t, c in responses if c]
        incorrect = [(t, c) for t, c in responses if not c]

        if not correct or not incorrect:
            return None

        mean_correct = sum(t for t, _ in correct) / len(correct)
        mean_incorrect = sum(t for t, _ in incorrect) / len(incorrect)

        # b = midpoint of the two group means
        b_estimate = (mean_correct + mean_incorrect) / 2.0

        # a is inversely related to the spread; narrower spread -> higher discrimination
        spread = mean_correct - mean_incorrect
        a_estimate = max(0.3, min(3.0, 1.7 / max(abs(spread), 0.1)))

        return a_estimate, b_estimate
