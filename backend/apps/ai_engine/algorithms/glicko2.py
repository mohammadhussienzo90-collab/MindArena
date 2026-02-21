"""
Glicko-2 Rating System
=======================
Full implementation of the Glicko-2 algorithm for competitive matchmaking
in MindArena's arena mode.

The Glicko-2 system (Glickman, 2012) extends Elo with two additional
parameters per player:

* **Rating deviation (RD)** -- confidence in the rating estimate. High RD
  means the system is uncertain; low RD means the rating is well-established.
* **Volatility (sigma)** -- expected fluctuation in a player's true skill
  level over time. Players who perform inconsistently have higher volatility.

Algorithm overview
------------------
1. Convert ratings to the Glicko-2 internal scale (mu, phi).
2. Compute the quantities v (variance) and delta (improvement).
3. Determine new volatility sigma' using the Illinois algorithm
   (a bracketed root-finding method for the volatility equation).
4. Update phi (rating deviation) and mu (rating).
5. Convert back to the Glicko-1 scale for display.

Constants
---------
TAU     = 0.5       System constant constraining volatility change.
                    Smaller = more conservative. Glickman recommends 0.3-1.2.
EPSILON = 0.000001  Convergence threshold for the Illinois algorithm.
SCALE   = 173.7178  Conversion factor: Glicko-2 = (Glicko-1 - 1500) / SCALE.

References
----------
- Glickman, M. E. (2012). Example of the Glicko-2 System.
  http://www.glicko.net/glicko/glicko2.pdf
- Used by Lichess, Pokemon Showdown, and many competitive platforms.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

# ======================================================================
# Constants
# ======================================================================
TAU: float = 0.5
EPSILON: float = 0.000001
SCALE: float = 173.7178

# Default values for new players (Glicko-1 scale)
DEFAULT_RATING: float = 1500.0
DEFAULT_RD: float = 350.0
DEFAULT_SIGMA: float = 0.06


# ======================================================================
# Scale conversions
# ======================================================================
def to_glicko2_scale(rating: float, rd: float) -> Tuple[float, float]:
    """Convert from Glicko-1 scale to Glicko-2 internal scale.

    Parameters
    ----------
    rating : float
        Glicko-1 rating (centred at 1500).
    rd : float
        Glicko-1 rating deviation.

    Returns
    -------
    (mu, phi) : tuple of float
        Glicko-2 internal values.
    """
    mu = (rating - 1500.0) / SCALE
    phi = rd / SCALE
    return mu, phi


def to_glicko1_scale(mu: float, phi: float) -> Tuple[float, float]:
    """Convert from Glicko-2 internal scale back to Glicko-1 scale.

    Parameters
    ----------
    mu : float
        Glicko-2 internal rating.
    phi : float
        Glicko-2 internal rating deviation.

    Returns
    -------
    (rating, rd) : tuple of float
        Glicko-1 rating and rating deviation.
    """
    rating = mu * SCALE + 1500.0
    rd = phi * SCALE
    return rating, rd


# ======================================================================
# Core Glicko-2 functions
# ======================================================================
def g(phi: float) -> float:
    """The g(phi) function from the Glicko-2 paper.

    Reduces the impact of games against opponents with high rating deviation.

    .. math::
        g(\\phi) = \\frac{1}{\\sqrt{1 + 3 \\phi^2 / \\pi^2}}

    Parameters
    ----------
    phi : float
        Opponent's rating deviation on the Glicko-2 scale.

    Returns
    -------
    float
        Value in (0, 1].
    """
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi * math.pi))


def E(mu: float, mu_j: float, phi_j: float) -> float:
    """Expected score (win probability) against an opponent.

    .. math::
        E(\\mu, \\mu_j, \\phi_j) = \\frac{1}{1 + \\exp(-g(\\phi_j)(\\mu - \\mu_j))}

    Parameters
    ----------
    mu : float
        Player's rating on the Glicko-2 scale.
    mu_j : float
        Opponent's rating on the Glicko-2 scale.
    phi_j : float
        Opponent's rating deviation on the Glicko-2 scale.

    Returns
    -------
    float
        Expected score in (0, 1).
    """
    return 1.0 / (1.0 + math.exp(-g(phi_j) * (mu - mu_j)))


def _compute_v(mu: float, opponents: List[Tuple[float, float, float]]) -> float:
    """Compute the estimated variance of the player's rating based only
    on game outcomes (Step 3 in the Glicko-2 paper).

    .. math::
        v = \\left[ \\sum_j g(\\phi_j)^2 \\cdot E_j \\cdot (1 - E_j) \\right]^{-1}

    Parameters
    ----------
    mu : float
        Player's current Glicko-2 rating.
    opponents : list of (mu_j, phi_j, score_j)
        Each tuple contains the opponent's Glicko-2 rating, rating deviation,
        and the actual game outcome (1 = win, 0.5 = draw, 0 = loss).

    Returns
    -------
    float
        Estimated variance v.
    """
    total = 0.0
    for mu_j, phi_j, _ in opponents:
        g_val = g(phi_j)
        e_val = E(mu, mu_j, phi_j)
        total += g_val * g_val * e_val * (1.0 - e_val)

    if total < EPSILON:
        return 1.0 / EPSILON

    return 1.0 / total


def _compute_delta(
    mu: float,
    opponents: List[Tuple[float, float, float]],
    v: float,
) -> float:
    """Compute the estimated improvement in rating (Step 4).

    .. math::
        \\Delta = v \\sum_j g(\\phi_j)(s_j - E_j)

    Parameters
    ----------
    mu : float
        Player's current Glicko-2 rating.
    opponents : list of (mu_j, phi_j, score_j)
    v : float
        Estimated variance from ``_compute_v``.

    Returns
    -------
    float
        Estimated improvement delta.
    """
    total = 0.0
    for mu_j, phi_j, score_j in opponents:
        g_val = g(phi_j)
        e_val = E(mu, mu_j, phi_j)
        total += g_val * (score_j - e_val)

    return v * total


# ======================================================================
# Volatility estimation (Illinois algorithm)
# ======================================================================
def _new_volatility(
    sigma: float,
    phi: float,
    v: float,
    delta: float,
    tau: float = TAU,
) -> float:
    """Determine the new volatility sigma' using the Illinois algorithm
    (Step 5 of the Glicko-2 paper).

    This solves for sigma' such that f(sigma') = 0, where f is defined
    in Section 5.4 of Glickman's paper. The Illinois method is a
    modification of the regula falsi (false position) method that
    guarantees convergence.

    Parameters
    ----------
    sigma : float
        Current volatility.
    phi : float
        Current rating deviation (Glicko-2 scale).
    v : float
        Estimated variance from game outcomes.
    delta : float
        Estimated improvement from game outcomes.
    tau : float
        System constant constraining volatility change.

    Returns
    -------
    float
        New volatility sigma'.
    """
    a = math.log(sigma * sigma)
    phi_sq = phi * phi
    delta_sq = delta * delta

    def f(x: float) -> float:
        """The function whose root we seek."""
        ex = math.exp(x)
        d = phi_sq + v + ex
        return (
            (ex * (delta_sq - phi_sq - v - ex)) / (2.0 * d * d)
            - (x - a) / (tau * tau)
        )

    # Step 5.2: Set initial values for the Illinois algorithm
    # A = a (lower bound)
    A = a

    # B: upper bound -- depends on whether delta^2 > phi^2 + v
    if delta_sq > phi_sq + v:
        B = math.log(delta_sq - phi_sq - v)
    else:
        k = 1
        while f(a - k * tau) < 0:
            k += 1
        B = a - k * tau

    # Step 5.3: Evaluate f at the boundaries
    f_A = f(A)
    f_B = f(B)

    # Step 5.4: Illinois algorithm iteration
    iterations = 0
    max_iterations = 100  # Safety limit

    while abs(B - A) > EPSILON and iterations < max_iterations:
        iterations += 1

        # Regula falsi step
        C = A + (A - B) * f_A / (f_B - f_A)
        f_C = f(C)

        if f_C * f_B <= 0:
            # Root is between C and B
            A = B
            f_A = f_B
        else:
            # Illinois modification: halve f_A to force convergence
            f_A = f_A / 2.0

        B = C
        f_B = f_C

    new_sigma = math.exp(A / 2.0)
    return new_sigma


# ======================================================================
# Main rating update
# ======================================================================
def update_rating(
    rating: float,
    rd: float,
    sigma: float,
    opponents: List[Tuple[float, float, float]],
    tau: float = TAU,
) -> Tuple[float, float, float]:
    """Full Glicko-2 rating update after a rating period.

    This implements the complete 8-step algorithm from the Glicko-2 paper.

    Parameters
    ----------
    rating : float
        Player's current Glicko-1 rating.
    rd : float
        Player's current Glicko-1 rating deviation.
    sigma : float
        Player's current volatility.
    opponents : list of (opp_rating, opp_rd, score)
        Each tuple contains the opponent's Glicko-1 rating, Glicko-1 rating
        deviation, and the actual game outcome:
        1.0 = win, 0.5 = draw, 0.0 = loss.
    tau : float
        System constant (default: TAU = 0.5).

    Returns
    -------
    (new_rating, new_rd, new_sigma) : tuple of float
        Updated Glicko-1 rating, rating deviation, and volatility.

    Examples
    --------
    >>> # Example from Glickman's paper
    >>> update_rating(1500, 200, 0.06, [
    ...     (1400, 30, 1.0),   # Beat a 1400-rated player
    ...     (1550, 100, 0.0),  # Lost to a 1550-rated player
    ...     (1700, 300, 0.0),  # Lost to a 1700-rated player
    ... ])
    (1464.06, 151.52, 0.05999)  # Approximate values
    """
    # Step 1: Convert to Glicko-2 scale
    mu, phi = to_glicko2_scale(rating, rd)

    # Convert opponents to Glicko-2 scale
    opp_g2: List[Tuple[float, float, float]] = []
    for opp_rating, opp_rd, score in opponents:
        opp_mu, opp_phi = to_glicko2_scale(opp_rating, opp_rd)
        opp_g2.append((opp_mu, opp_phi, score))

    # Handle the case where the player has no opponents this period
    if not opp_g2:
        # Step 6 (special case): Only update phi based on volatility
        phi_star = math.sqrt(phi * phi + sigma * sigma)
        new_rating, new_rd = to_glicko1_scale(mu, phi_star)
        return round(new_rating, 2), round(new_rd, 2), round(sigma, 5)

    # Step 3: Compute v (estimated variance)
    v = _compute_v(mu, opp_g2)

    # Step 4: Compute delta (estimated improvement)
    delta = _compute_delta(mu, opp_g2, v)

    # Step 5: Determine new volatility sigma'
    new_sigma = _new_volatility(sigma, phi, v, delta, tau)

    # Step 6: Update phi to the pre-rating-period value phi*
    phi_star = math.sqrt(phi * phi + new_sigma * new_sigma)

    # Step 7: Update phi and mu
    new_phi = 1.0 / math.sqrt(1.0 / (phi_star * phi_star) + 1.0 / v)

    # Step 8: Update mu
    update_sum = 0.0
    for mu_j, phi_j, score_j in opp_g2:
        g_val = g(phi_j)
        e_val = E(mu, mu_j, phi_j)
        update_sum += g_val * (score_j - e_val)

    new_mu = mu + new_phi * new_phi * update_sum

    # Convert back to Glicko-1 scale
    new_rating, new_rd = to_glicko1_scale(new_mu, new_phi)

    return round(new_rating, 2), round(new_rd, 2), round(new_sigma, 5)


# ======================================================================
# Match quality assessment
# ======================================================================
def match_quality(
    p1_rating: float,
    p1_rd: float,
    p2_rating: float,
    p2_rd: float,
) -> float:
    """Compute match quality (balance) between two players.

    Uses the draw probability under the Glicko-2 model as a proxy for
    match balance. A perfectly balanced match (equal ratings, low RDs)
    yields a quality near 1.0.

    The formula is based on the expected draw probability:

    .. math::
        q = \\exp\\left(-\\frac{(\\mu_1 - \\mu_2)^2}{2(\\phi_1^2 + \\phi_2^2 + 2 \\cdot \\beta^2)}\\right)

    where beta^2 = SCALE^2 / (2 * ln(10)) represents the performance
    variance of a single game.

    Parameters
    ----------
    p1_rating, p1_rd : float
        Player 1's Glicko-1 rating and rating deviation.
    p2_rating, p2_rd : float
        Player 2's Glicko-1 rating and rating deviation.

    Returns
    -------
    float
        Match quality in [0, 1]. Values above 0.4 indicate a fair match.
    """
    mu1, phi1 = to_glicko2_scale(p1_rating, p1_rd)
    mu2, phi2 = to_glicko2_scale(p2_rating, p2_rd)

    # Beta squared: variance of a single game performance
    beta_sq = (SCALE * SCALE) / (2.0 * math.log(10))
    # On the Glicko-2 scale, beta_sq_g2 = beta_sq / SCALE^2
    beta_sq_g2 = 1.0 / (2.0 * math.log(10))

    rating_diff_sq = (mu1 - mu2) * (mu1 - mu2)
    combined_var = phi1 * phi1 + phi2 * phi2 + 2.0 * beta_sq_g2

    quality = math.exp(-rating_diff_sq / (2.0 * combined_var))
    return round(max(0.0, min(1.0, quality)), 4)


# ======================================================================
# Win probability
# ======================================================================
def win_probability(
    p1_rating: float,
    p1_rd: float,
    p2_rating: float,
    p2_rd: float,
) -> float:
    """Compute the probability that player 1 beats player 2.

    Parameters
    ----------
    p1_rating, p1_rd : float
        Player 1's Glicko-1 rating and rating deviation.
    p2_rating, p2_rd : float
        Player 2's Glicko-1 rating and rating deviation.

    Returns
    -------
    float
        Win probability for player 1 in [0, 1].
    """
    mu1, phi1 = to_glicko2_scale(p1_rating, p1_rd)
    mu2, phi2 = to_glicko2_scale(p2_rating, p2_rd)
    return E(mu1, mu2, phi2)


# ======================================================================
# Rating period decay
# ======================================================================
def decay_rd(rd: float, sigma: float, periods: int = 1) -> float:
    """Increase RD for a player who has not played in one or more rating
    periods (accounting for growing uncertainty).

    Parameters
    ----------
    rd : float
        Current Glicko-1 rating deviation.
    sigma : float
        Current volatility.
    periods : int
        Number of rating periods elapsed without play.

    Returns
    -------
    float
        Updated rating deviation, capped at DEFAULT_RD.
    """
    _, phi = to_glicko2_scale(0, rd)  # We only need phi

    for _ in range(periods):
        phi = math.sqrt(phi * phi + sigma * sigma)

    _, new_rd = to_glicko1_scale(0, phi)
    return round(min(new_rd, DEFAULT_RD), 2)


# ======================================================================
# Django integration helpers
# ======================================================================
def process_arena_match(
    player1_stats: Dict,
    player2_stats: Dict,
    outcome: float,
) -> Tuple[Dict, Dict]:
    """Process a MindArena arena match and return updated stats for both
    players.

    Parameters
    ----------
    player1_stats : dict
        Must contain ``rating`` (float), ``rd`` (float), ``sigma`` (float).
    player2_stats : dict
        Same structure as player1_stats.
    outcome : float
        Result from player 1's perspective: 1.0 = P1 wins, 0.5 = draw,
        0.0 = P1 loses.

    Returns
    -------
    (p1_updated, p2_updated) : tuple of dict
        Updated stats for each player, including ``rating``, ``rd``,
        ``sigma``, ``rating_change``, and ``rd_change``.
    """
    p1_r = player1_stats.get('rating', DEFAULT_RATING)
    p1_rd = player1_stats.get('rd', DEFAULT_RD)
    p1_sigma = player1_stats.get('sigma', DEFAULT_SIGMA)

    p2_r = player2_stats.get('rating', DEFAULT_RATING)
    p2_rd = player2_stats.get('rd', DEFAULT_RD)
    p2_sigma = player2_stats.get('sigma', DEFAULT_SIGMA)

    # Update player 1
    new_r1, new_rd1, new_s1 = update_rating(
        p1_r, p1_rd, p1_sigma,
        [(p2_r, p2_rd, outcome)],
    )

    # Update player 2 (inverse outcome)
    new_r2, new_rd2, new_s2 = update_rating(
        p2_r, p2_rd, p2_sigma,
        [(p1_r, p1_rd, 1.0 - outcome)],
    )

    p1_updated = {
        'rating': new_r1,
        'rd': new_rd1,
        'sigma': new_s1,
        'rating_change': round(new_r1 - p1_r, 2),
        'rd_change': round(new_rd1 - p1_rd, 2),
    }

    p2_updated = {
        'rating': new_r2,
        'rd': new_rd2,
        'sigma': new_s2,
        'rating_change': round(new_r2 - p2_r, 2),
        'rd_change': round(new_rd2 - p2_rd, 2),
    }

    return p1_updated, p2_updated


def find_best_match(
    player_rating: float,
    player_rd: float,
    candidates: List[Tuple[int, float, float]],
    min_quality: float = 0.3,
) -> Optional[Tuple[int, float]]:
    """Find the best opponent for a player from a list of candidates.

    Parameters
    ----------
    player_rating : float
        The searching player's Glicko-1 rating.
    player_rd : float
        The searching player's rating deviation.
    candidates : list of (player_id, rating, rd)
        Available opponents.
    min_quality : float
        Minimum acceptable match quality (default: 0.3).

    Returns
    -------
    (player_id, quality) or None
        The best match, or None if no candidate meets the minimum quality.
    """
    best_id: Optional[int] = None
    best_quality: float = -1.0

    for cand_id, cand_rating, cand_rd in candidates:
        q = match_quality(player_rating, player_rd, cand_rating, cand_rd)
        if q > best_quality:
            best_quality = q
            best_id = cand_id

    if best_quality >= min_quality and best_id is not None:
        return best_id, round(best_quality, 4)

    return None
