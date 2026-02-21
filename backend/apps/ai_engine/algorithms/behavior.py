"""
Player Behavior Analytics Engine
=================================
Flow detection, emotion inference, engagement scoring, churn prediction,
and Bartle player-type classification.

References
----------
- Csikszentmihalyi, M. (1990). *Flow: The Psychology of Optimal Experience*.
- Bartle, R. (1996). Hearts, Clubs, Diamonds, Spades: Players Who Suit MUDs.
"""
import math
from datetime import timedelta

from django.utils import timezone


class BehaviorEngine:
    """Stateless analytics class -- every method is a pure @staticmethod."""

    # ------------------------------------------------------------------
    # Session-level analysis
    # ------------------------------------------------------------------
    @staticmethod
    def analyze_session(results):
        """Analyse a play session from a list of challenge results.

        Parameters
        ----------
        results : list[dict]
            Each dict must contain at least ``is_correct`` (bool),
            ``time_taken_secs`` (float), and ``score`` (int).

        Returns
        -------
        dict
            ``flow_score`` 0-1, ``inferred_emotion`` str,
            ``accuracy`` 0-1, ``response_time_cv`` >= 0,
            ``accuracy_trend`` -1..+1, ``mean_response_time`` secs.
        """
        if not results:
            return {
                'flow_score': 0,
                'inferred_emotion': 'neutral',
                'accuracy': 0,
                'response_time_cv': 0,
                'accuracy_trend': 0,
                'mean_response_time': 0,
            }

        times = [r['time_taken_secs'] for r in results if r.get('time_taken_secs')]
        accuracies = [1 if r['is_correct'] else 0 for r in results]

        # Response-time statistics
        mean_time = sum(times) / len(times) if times else 0
        variance = (
            sum((t - mean_time) ** 2 for t in times) / len(times)
            if times
            else 0
        )
        cv = math.sqrt(variance) / max(mean_time, 0.1) if times else 0

        # Accuracy
        accuracy = sum(accuracies) / len(accuracies) if accuracies else 0

        # Accuracy trend (split-half comparison)
        accuracy_trend = 0
        if len(accuracies) >= 4:
            mid = len(accuracies) // 2
            first_half = sum(accuracies[:mid]) / mid
            second_half = sum(accuracies[mid:]) / (len(accuracies) - mid)
            accuracy_trend = second_half - first_half

        flow_score = BehaviorEngine._calculate_flow(
            accuracy, cv, accuracy_trend, len(results),
        )
        emotion = BehaviorEngine._infer_emotion(
            accuracy, cv, accuracy_trend, flow_score,
        )

        return {
            'flow_score': round(flow_score, 3),
            'inferred_emotion': emotion,
            'accuracy': round(accuracy, 3),
            'response_time_cv': round(cv, 3),
            'accuracy_trend': round(accuracy_trend, 3),
            'mean_response_time': round(mean_time, 2),
        }

    # ------------------------------------------------------------------
    # Flow (Csikszentmihalyi)
    # ------------------------------------------------------------------
    @staticmethod
    def _calculate_flow(accuracy, cv, trend, n):
        """Compute a flow score (0-1) using four sub-signals.

        * **Difficulty match** (35 %) -- peaks near 70 % accuracy.
        * **Consistency** (30 %) -- low response-time variability.
        * **Engagement** (20 %) -- longer sessions correlate with flow.
        * **Trend bonus** (15 %) -- improving accuracy is a flow signal.
        """
        # Optimal difficulty zone centred at 70 % accuracy
        diff_score = max(0, min(1, 1.0 - abs(accuracy - 0.70) / 0.30))

        # Response-time coefficient of variation below 1.5 is consistent
        consistency = max(0, 1.0 - cv / 1.5)

        # Trend bonus (positive trend capped at 0.2)
        trend_bonus = max(0, min(0.2, trend * 0.5))

        # Engagement: ramp to 1.0 over first 10 challenges
        engagement = min(1.0, n / 10)

        raw = (
            diff_score * 0.35
            + consistency * 0.30
            + engagement * 0.20
            + trend_bonus * 0.15
        )
        return max(0, min(1, raw))

    # ------------------------------------------------------------------
    # Emotion inference
    # ------------------------------------------------------------------
    @staticmethod
    def _infer_emotion(accuracy, cv, trend, flow_score):
        """Map behavioural signals to a discrete emotional state.

        Returns one of: ``flow``, ``bored``, ``frustrated``,
        ``anxious``, ``engaged``, ``neutral``.
        """
        if flow_score >= 0.7:
            return 'flow'
        if accuracy > 0.9 and cv < 0.3:
            return 'bored'
        if accuracy < 0.3 and cv > 0.8:
            return 'frustrated'
        if accuracy < 0.5 and trend < -0.2:
            return 'anxious'
        if trend > 0.15:
            return 'engaged'
        return 'neutral'

    # ------------------------------------------------------------------
    # Engagement (composite weekly score)
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_engagement_score(player):
        """Return a 0-1 composite engagement score.

        Weights
        -------
        * Frequency   30 % -- sessions per week (target: 7).
        * Length       20 % -- average session length (optimal: 20 min).
        * Streak       20 % -- current daily streak (target: 14 days).
        * Diversity   15 % -- distinct realms played this week.
        * Social      15 % -- companion messages this week.
        """
        from apps.ai_engine.models import PlayerSession
        from apps.companion.models import CompanionMessage
        from apps.progression.models import PlayerChallengeResult

        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # --- Frequency (30 %) ---
        recent_sessions = PlayerSession.objects.filter(
            player=player, started_at__gte=week_ago,
        ).count()
        freq_score = min(1.0, recent_sessions / 7.0)

        # --- Session length (20 %) ---
        from django.db.models import Avg

        avg_length = (
            PlayerSession.objects.filter(
                player=player, started_at__gte=month_ago,
            ).aggregate(avg=Avg('duration_secs'))['avg']
            or 0
        )
        # Optimal session = 1200 s (20 min); penalise deviation up to 1800 s
        length_score = max(0, min(1, 1.0 - abs(avg_length - 1200) / 1800))

        # --- Streak (20 %) ---
        try:
            streak = player.streak
            streak_score = min(1.0, streak.current_streak / 14)
        except Exception:
            streak_score = 0

        # --- Diversity (15 %) ---
        recent_realms = (
            PlayerChallengeResult.objects.filter(
                player=player, played_at__gte=week_ago,
            )
            .values('challenge__quest__realm')
            .distinct()
            .count()
        )
        diversity_score = min(1.0, recent_realms / 4)

        # --- Social / Companion (15 %) ---
        companion_msgs = CompanionMessage.objects.filter(
            conversation__player=player,
            created_at__gte=week_ago,
            role='player',
        ).count()
        social_score = min(1.0, companion_msgs / 10)

        composite = (
            freq_score * 0.30
            + length_score * 0.20
            + streak_score * 0.20
            + diversity_score * 0.15
            + social_score * 0.15
        )
        return round(max(0, min(1, composite)), 3)

    # ------------------------------------------------------------------
    # Churn prediction (logistic model)
    # ------------------------------------------------------------------
    @staticmethod
    def predict_churn(player):
        """Return a 0-1 churn probability using a simple logistic model.

        Features
        --------
        * ``days_inactive`` -- days since last activity.
        * ``engagement`` -- composite engagement score.
        * ``streak_broken`` -- whether a long streak was recently broken.

        The coefficients were hand-tuned from play-test data and can be
        replaced with a trained model later.
        """
        now = timezone.now()
        days_inactive = (now - (player.last_active_at or player.created_at)).days
        engagement = BehaviorEngine.calculate_engagement_score(player)

        try:
            streak = player.streak
            streak_broken = streak.current_streak == 0 and streak.longest_streak > 3
        except Exception:
            streak_broken = False

        # z = w1*days + w2*engagement + w3*streak_broken + bias
        z = (
            0.3 * days_inactive
            + (-3.0) * engagement
            + 1.5 * (1 if streak_broken else 0)
            - 0.5
        )
        probability = 1.0 / (1.0 + math.exp(-z))
        return round(max(0, min(1, probability)), 3)

    # ------------------------------------------------------------------
    # Player-type classification (Bartle taxonomy variant)
    # ------------------------------------------------------------------
    @staticmethod
    def classify_player_type(player):
        """Classify a player as one of four types based on behaviour.

        Returns
        -------
        str
            One of ``achiever``, ``explorer``, ``socializer``,
            ``completionist``.
        """
        from apps.arena.models import PlayerArenaStats
        from apps.companion.models import CompanionMessage
        from apps.progression.models import PlayerChallengeResult, PlayerRealmStat

        # --- Achiever: XP + streak focus ---
        try:
            streak = player.streak.current_streak
        except Exception:
            streak = 0
        achiever = (
            min(1.0, player.total_xp / 5000) * 0.5
            + min(1.0, streak / 14) * 0.5
        )

        # --- Explorer: diversity of realms ---
        realms_active = PlayerRealmStat.objects.filter(
            player=player, challenges_completed__gt=0,
        ).count()
        explorer = min(1.0, realms_active / 6)

        # --- Socializer: companion interactions + arena ---
        msgs = CompanionMessage.objects.filter(
            conversation__player=player, role='player',
        ).count()
        try:
            arena = PlayerArenaStats.objects.get(player=player).matches_played
        except Exception:
            arena = 0
        socializer = min(1.0, (msgs + arena * 5) / 50)

        # --- Completionist: perfect scores ---
        total = PlayerChallengeResult.objects.filter(player=player).count()
        perfect = PlayerChallengeResult.objects.filter(
            player=player, score=100,
        ).count()
        completionist = perfect / max(total, 1)

        scores = {
            'achiever': achiever,
            'explorer': explorer,
            'socializer': socializer,
            'completionist': completionist,
        }
        return max(scores, key=scores.get)
