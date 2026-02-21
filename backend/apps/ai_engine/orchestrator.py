"""
Central AI Orchestrator
========================
Coordinates all AI algorithms (IRT, FSRS, BKT, behavior, recommender,
learning path) and the Smart Noor companion into a single coherent API
that the rest of the application can call.

Every public method on AIOrchestrator is a high-level action that
delegates to the appropriate algorithm(s) and persists results to the
database.  All methods are classmethods so no instantiation is needed.
"""
import logging
from datetime import timedelta

from django.db.models import Avg
from django.utils import timezone

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """Central coordinator for all MindArena AI subsystems."""

    # ------------------------------------------------------------------
    # Hook: challenge completed
    # ------------------------------------------------------------------

    @classmethod
    def on_challenge_completed(cls, player, challenge, result):
        """Hook called after a player completes a challenge.

        Delegates to IRT, FSRS, BKT, challenge stats, and session
        updates.  Each sub-update is wrapped in its own try/except so
        a failure in one algorithm does not block the others.

        Parameters
        ----------
        player : Player
            The player who completed the challenge.
        challenge : Challenge
            The challenge that was completed.
        result : dict
            Must contain: score (int 0-100), is_correct (bool),
            time_taken_secs (float), xp_earned (int).
        """
        try:
            cls._update_irt(player, challenge, result)
        except Exception as e:
            logger.error("IRT update failed for player %s: %s", player.id, e)

        try:
            cls._update_fsrs(player, challenge, result)
        except Exception as e:
            logger.error("FSRS update failed for player %s: %s", player.id, e)

        try:
            cls._update_bkt(player, challenge, result)
        except Exception as e:
            logger.error("BKT update failed for player %s: %s", player.id, e)

        try:
            cls._update_challenge_stats(challenge, result)
        except Exception as e:
            logger.error("Challenge stats update failed for challenge %s: %s", challenge.id, e)

        try:
            cls._update_session(player, result)
        except Exception as e:
            logger.error("Session update failed for player %s: %s", player.id, e)

    # ------------------------------------------------------------------
    # Hook: session lifecycle
    # ------------------------------------------------------------------

    @classmethod
    def on_session_start(cls, player):
        """Create a new AI-monitored play session.

        Parameters
        ----------
        player : Player

        Returns
        -------
        int
            The session ID.
        """
        from apps.ai_engine.models import PlayerSession

        session = PlayerSession.objects.create(player=player)
        logger.info("Session %s started for player %s", session.id, player.id)
        return session.id

    @classmethod
    def on_session_end(cls, player, session_id):
        """End a play session and compute session-level analytics.

        Parameters
        ----------
        player : Player
        session_id : int

        Returns
        -------
        dict
            Session summary with flow_score, inferred_emotion, duration,
            accuracy, and engagement update.
        """
        from apps.ai_engine.algorithms.behavior import BehaviorEngine
        from apps.ai_engine.models import PlayerEngagement, PlayerSession
        from apps.progression.models import PlayerChallengeResult

        try:
            session = PlayerSession.objects.get(id=session_id, player=player)
        except PlayerSession.DoesNotExist:
            logger.warning("Session %s not found for player %s", session_id, player.id)
            return {'error': 'Session not found'}

        now = timezone.now()
        session.ended_at = now
        session.duration_secs = (now - session.started_at).total_seconds()

        # Gather challenge results during this session
        results = list(
            PlayerChallengeResult.objects.filter(
                player=player,
                played_at__gte=session.started_at,
                played_at__lte=now,
            ).values(
                'is_correct', 'time_taken_secs', 'score',
                'challenge__quest__realm__slug',
            )
        )

        session.challenges_attempted = len(results)
        session.challenges_correct = sum(1 for r in results if r['is_correct'])

        # Calculate response time stats
        times = [r['time_taken_secs'] for r in results if r['time_taken_secs'] > 0]
        if times:
            session.avg_response_time = sum(times) / len(times)
            mean = session.avg_response_time
            session.response_time_variance = sum((t - mean) ** 2 for t in times) / len(times)
        else:
            session.avg_response_time = 0
            session.response_time_variance = 0

        # Track realms visited
        realms_visited = list(set(
            r['challenge__quest__realm__slug'] for r in results
            if r.get('challenge__quest__realm__slug')
        ))
        session.realms_visited = realms_visited

        # Detect abandonment (session ended with < 2 challenges in > 5 min)
        session.abandoned = (
            session.duration_secs > 300 and session.challenges_attempted < 2
        )

        # Analyze session behavior
        behavior_results = [
            {
                'is_correct': r['is_correct'],
                'time_taken_secs': r['time_taken_secs'],
                'score': r['score'],
            }
            for r in results
        ]
        analysis = BehaviorEngine.analyze_session(behavior_results)
        session.flow_score = analysis.get('flow_score', 0)
        session.inferred_emotion = analysis.get('inferred_emotion', 'neutral')

        session.save()

        # Update engagement metrics
        engagement_score = BehaviorEngine.calculate_engagement_score(player)
        churn_risk = BehaviorEngine.predict_churn(player)

        engagement, _ = PlayerEngagement.objects.get_or_create(player=player)
        engagement.engagement_score = engagement_score
        engagement.churn_risk = churn_risk

        # Update session stats on engagement
        recent_sessions = PlayerSession.objects.filter(
            player=player,
            ended_at__isnull=False,
            started_at__gte=now - timedelta(days=30),
        )
        avg_len = recent_sessions.aggregate(avg=Avg('duration_secs'))['avg'] or 0
        engagement.avg_session_length_secs = avg_len

        week_sessions = recent_sessions.filter(
            started_at__gte=now - timedelta(days=7),
        ).count()
        engagement.sessions_per_week = week_sessions

        # Determine preferred time of day from recent sessions
        hours = list(
            PlayerSession.objects.filter(
                player=player,
                started_at__gte=now - timedelta(days=30),
            ).values_list('started_at', flat=True)
        )
        if hours:
            hour_counts = {}
            for dt in hours:
                h = dt.hour
                hour_counts[h] = hour_counts.get(h, 0) + 1
            engagement.preferred_time_of_day = max(hour_counts, key=hour_counts.get)

        # Classify personality cluster
        engagement.personality_cluster = BehaviorEngine.classify_player_type(player)

        engagement.save()

        return {
            'session_id': session.id,
            'duration_secs': round(session.duration_secs, 1),
            'challenges_attempted': session.challenges_attempted,
            'challenges_correct': session.challenges_correct,
            'flow_score': session.flow_score,
            'inferred_emotion': session.inferred_emotion,
            'abandoned': session.abandoned,
            'engagement_score': engagement_score,
            'churn_risk': churn_risk,
        }

    # ------------------------------------------------------------------
    # Public: get next challenge
    # ------------------------------------------------------------------

    @classmethod
    def get_next_challenge(cls, player, realm_slug=None):
        """Get the AI-recommended next challenge for a player.

        Parameters
        ----------
        player : Player
        realm_slug : str, optional
            If provided, restrict recommendations to this realm.

        Returns
        -------
        dict or None
            Challenge recommendation with score breakdown, or None if
            no candidates found.
        """
        from apps.ai_engine.algorithms.recommender import hybrid_recommend
        from apps.ai_engine.models import RecommendationLog

        recommendations = hybrid_recommend(player, n=1, candidate_limit=100)

        # Filter by realm if specified
        if realm_slug and recommendations:
            # Re-run with realm filter
            from apps.realms.models import Challenge
            from apps.ai_engine.algorithms.recommender import (
                SIGNAL_WEIGHTS, _bkt_score, _exploration_score,
                _fsrs_score, _irt_score, _thompson_score,
                content_based_score,
            )
            from apps.ai_engine.models import PlayerAbility

            try:
                ability = PlayerAbility.objects.filter(
                    player=player
                ).order_by('-last_updated').first()
                player_ability = ability.theta if ability else 0.0
            except Exception:
                player_ability = 0.0

            try:
                assessment = player.assessment
            except Exception:
                assessment = None

            candidates = (
                Challenge.objects
                .filter(is_active=True, quest__realm__slug=realm_slug)
                .select_related('quest', 'quest__realm')
                .order_by('?')[:100]
            )

            scored = []
            for challenge in candidates:
                signals = {
                    'irt': _irt_score(player_ability, challenge.difficulty),
                    'bkt': _bkt_score(player, challenge),
                    'content': content_based_score(assessment, challenge) if assessment else 0.5,
                    'fsrs': _fsrs_score(player, challenge),
                    'thompson': _thompson_score(player, challenge),
                    'exploration': _exploration_score(),
                }
                composite = sum(
                    signals[key] * SIGNAL_WEIGHTS[key] for key in SIGNAL_WEIGHTS
                )
                scored.append({
                    'challenge': challenge,
                    'challenge_id': challenge.id,
                    'composite_score': round(composite, 4),
                    'signals': {k: round(v, 4) for k, v in signals.items()},
                })

            scored.sort(key=lambda x: x['composite_score'], reverse=True)
            recommendations = scored[:1]

        if not recommendations:
            return None

        top = recommendations[0]
        challenge = top['challenge']

        # Log the recommendation
        RecommendationLog.objects.create(
            player=player,
            challenge=challenge,
            recommendation_source='hybrid',
            score=top['composite_score'],
        )

        return {
            'challenge_id': challenge.id,
            'challenge_slug': challenge.slug,
            'title_en': challenge.title_en,
            'title_ar': getattr(challenge, 'title_ar', ''),
            'challenge_type': challenge.challenge_type,
            'difficulty': challenge.difficulty,
            'primary_trait': challenge.primary_trait,
            'time_limit_secs': challenge.time_limit_secs,
            'base_xp': challenge.base_xp,
            'bonus_xp': challenge.bonus_xp,
            'realm': challenge.quest.realm.slug if challenge.quest and challenge.quest.realm else None,
            'quest': challenge.quest.slug if challenge.quest else None,
            'ai_score': top['composite_score'],
            'ai_signals': top['signals'],
            'ai_explanation': cls._explain_recommendation(top['signals']),
        }

    # ------------------------------------------------------------------
    # Public: player insights
    # ------------------------------------------------------------------

    @classmethod
    def get_player_insights(cls, player):
        """Get comprehensive AI insights for the player dashboard.

        Returns
        -------
        dict
            Contains: knowledge_radar, flow_state, engagement, churn_risk,
            recommendations, learning_path, emotion_state, player_type,
            abilities, srs_summary.
        """
        from apps.ai_engine.algorithms.behavior import BehaviorEngine
        from apps.ai_engine.algorithms.bkt import BKTEngine
        from apps.ai_engine.algorithms.learning_path import generate_learning_path
        from apps.ai_engine.algorithms.recommender import hybrid_recommend
        from apps.ai_engine.models import (
            KnowledgeState, PlayerAbility, PlayerEngagement,
            PlayerSession, SpacedRepetitionCard,
        )

        now = timezone.now()

        # 1. Knowledge radar (BKT summary)
        knowledge_radar = BKTEngine.knowledge_summary(player)

        # 2. Flow state (from most recent session)
        latest_session = PlayerSession.objects.filter(
            player=player,
        ).order_by('-started_at').first()

        flow_state = {
            'flow_score': latest_session.flow_score if latest_session else 0,
            'inferred_emotion': latest_session.inferred_emotion if latest_session else 'neutral',
            'last_session_duration': latest_session.duration_secs if latest_session else 0,
        }

        # 3. Engagement & churn
        try:
            engagement_obj = PlayerEngagement.objects.get(player=player)
            engagement = {
                'engagement_score': engagement_obj.engagement_score,
                'churn_risk': engagement_obj.churn_risk,
                'preferred_time_of_day': engagement_obj.preferred_time_of_day,
                'avg_session_length_secs': engagement_obj.avg_session_length_secs,
                'sessions_per_week': engagement_obj.sessions_per_week,
                'personality_cluster': engagement_obj.personality_cluster,
            }
        except PlayerEngagement.DoesNotExist:
            engagement_score = BehaviorEngine.calculate_engagement_score(player)
            churn_risk = BehaviorEngine.predict_churn(player)
            engagement = {
                'engagement_score': engagement_score,
                'churn_risk': churn_risk,
                'preferred_time_of_day': 12,
                'avg_session_length_secs': 0,
                'sessions_per_week': 0,
                'personality_cluster': BehaviorEngine.classify_player_type(player),
            }

        # 4. Recommendations (top 3)
        try:
            recs = hybrid_recommend(player, n=3)
            recommendations = [
                {
                    'challenge_id': r['challenge_id'],
                    'title': r['challenge'].title_en,
                    'difficulty': r['challenge'].difficulty,
                    'composite_score': r['composite_score'],
                    'signals': r['signals'],
                }
                for r in recs
            ]
        except Exception as e:
            logger.error("Recommendation generation failed: %s", e)
            recommendations = []

        # 5. Learning path
        try:
            path = generate_learning_path(player)
        except Exception as e:
            logger.error("Learning path generation failed: %s", e)
            path = []

        # 6. Abilities (IRT theta)
        abilities = list(
            PlayerAbility.objects.filter(player=player).values(
                'skill', 'theta', 'theta_se', 'responses_count',
                'realm__slug', 'realm__name_en',
            )
        )

        # 7. SRS summary
        total_cards = SpacedRepetitionCard.objects.filter(player=player).count()
        due_cards = SpacedRepetitionCard.objects.filter(
            player=player, due_date__lte=now,
        ).count()
        srs_summary = {
            'total_cards': total_cards,
            'due_cards': due_cards,
            'review_load': round(due_cards / max(total_cards, 1), 3),
        }

        # 8. Skill gaps
        skill_gaps = BKTEngine.identify_gaps(player)[:5]

        # 9. Player type
        player_type = BehaviorEngine.classify_player_type(player)

        return {
            'knowledge_radar': knowledge_radar,
            'flow_state': flow_state,
            'engagement': engagement,
            'recommendations': recommendations,
            'learning_path': path[:5],
            'abilities': abilities,
            'srs_summary': srs_summary,
            'skill_gaps': [
                {'skill': skill, 'p_known': round(pk, 3)}
                for skill, pk in skill_gaps
            ],
            'player_type': player_type,
        }

    # ------------------------------------------------------------------
    # Public: companion chat
    # ------------------------------------------------------------------

    @classmethod
    def companion_chat(cls, player, message, context=None):
        """Generate a Smart Noor response (no external API).

        Parameters
        ----------
        player : Player
        message : str
        context : dict, optional

        Returns
        -------
        dict
            Keys: response, emotion, coaching_strategy, suggestions.
        """
        from apps.ai_engine.noor.engine import SmartNoorEngine

        # Enrich context with player data
        enriched_context = dict(context or {})

        # Add recent performance data
        from apps.progression.models import PlayerChallengeResult

        recent_results = PlayerChallengeResult.objects.filter(
            player=player,
        ).order_by('-played_at')[:10]

        if recent_results.exists():
            scores = [r.score for r in recent_results]
            enriched_context['recent_accuracy'] = sum(
                1 for r in recent_results if r.is_correct
            ) / len(scores)
            enriched_context['avg_difficulty'] = 5  # Default
            enriched_context['recent_avg_score'] = sum(scores) / len(scores)

        # Add streak info
        try:
            streak = player.streak
            enriched_context['streak'] = streak.current_streak
        except Exception:
            enriched_context['streak'] = 0

        return SmartNoorEngine.generate_response(player, message, enriched_context)

    # ------------------------------------------------------------------
    # Private: IRT update
    # ------------------------------------------------------------------

    @classmethod
    def _update_irt(cls, player, challenge, result):
        """Update IRT ability estimate after a challenge response.

        Gets or creates a PlayerAbility record for the challenge's
        primary_trait, then runs Newton-Raphson MLE to update theta.
        """
        from apps.ai_engine.algorithms.irt import IRTEngine
        from apps.ai_engine.models import ChallengeParameter, PlayerAbility

        skill = challenge.primary_trait
        realm = challenge.quest.realm if challenge.quest else None

        # Get or create player ability
        ability, created = PlayerAbility.objects.get_or_create(
            player=player,
            realm=realm,
            skill=skill,
            defaults={'theta': 0.0, 'theta_se': 1.0, 'responses_count': 0},
        )

        # Get challenge IRT parameters
        try:
            params = ChallengeParameter.objects.get(challenge=challenge)
            a = params.discrimination
            b = params.difficulty_b
            c = params.guessing_c
        except ChallengeParameter.DoesNotExist:
            # Auto-initialize from difficulty
            a = 1.0
            b = IRTEngine.initialize_from_difficulty(challenge.difficulty)
            c = 0.25 if challenge.challenge_type == 'multiple_choice' else 0.0
            ChallengeParameter.objects.create(
                challenge=challenge,
                discrimination=a,
                difficulty_b=b,
                guessing_c=c,
            )

        # Run IRT update
        is_correct = result.get('is_correct', False)
        responses = [(a, b, c, is_correct)]

        new_theta, new_se = IRTEngine.update_theta(
            ability.theta, ability.theta_se, responses,
        )

        ability.theta = new_theta
        ability.theta_se = new_se
        ability.responses_count += 1
        ability.save()

        logger.debug(
            "IRT updated: player=%s skill=%s theta=%.3f -> %.3f",
            player.id, skill, ability.theta - (new_theta - ability.theta), new_theta,
        )

    # ------------------------------------------------------------------
    # Private: FSRS update
    # ------------------------------------------------------------------

    @classmethod
    def _update_fsrs(cls, player, challenge, result):
        """Update FSRS spaced repetition card after a challenge response.

        Converts the challenge result to an FSRS rating (1-4) and runs
        the FSRS review algorithm to update scheduling.
        """
        from apps.ai_engine.algorithms.fsrs import FSRSEngine
        from apps.ai_engine.models import SpacedRepetitionCard

        now = timezone.now()

        # Get or create SRS card
        card, created = SpacedRepetitionCard.objects.get_or_create(
            player=player,
            challenge=challenge,
            defaults={
                'stability': 1.0,
                'difficulty_fsrs': 0.3,
                'state': SpacedRepetitionCard.STATE_NEW,
                'due_date': now,
            },
        )

        # Convert result to FSRS rating
        rating = FSRSEngine.rating_from_result(
            score=result.get('score', 0),
            time_taken=result.get('time_taken_secs', 0),
            time_limit=challenge.time_limit_secs,
        )

        # Build card state dict for FSRS
        if not created and card.last_review:
            elapsed = (now - card.last_review).total_seconds() / 86400.0
        else:
            elapsed = 0

        card_state = {
            'state': card.state,
            'stability': card.stability,
            'difficulty_fsrs': card.difficulty_fsrs,
            'elapsed_days': elapsed,
            'reps': card.reps,
            'lapses': card.lapses,
        }

        # Run FSRS review
        updated = FSRSEngine.review_card(card_state, rating)

        # Apply updates
        card.stability = updated['stability']
        card.difficulty_fsrs = updated['difficulty_fsrs']
        card.scheduled_days = updated['scheduled_days']
        card.elapsed_days = updated['elapsed_days']
        card.state = updated['state']
        card.due_date = updated['due_date']
        card.last_review = updated['last_review']
        card.reps = updated['reps']
        card.lapses = updated['lapses']
        card.save()

        logger.debug(
            "FSRS updated: player=%s challenge=%s rating=%d next_due=%s",
            player.id, challenge.id, rating, card.due_date,
        )

    # ------------------------------------------------------------------
    # Private: BKT update
    # ------------------------------------------------------------------

    @classmethod
    def _update_bkt(cls, player, challenge, result):
        """Update Bayesian Knowledge Tracing state for the challenge's
        primary skill.
        """
        from apps.ai_engine.algorithms.bkt import BKTEngine
        from apps.ai_engine.models import KnowledgeState

        skill = challenge.primary_trait

        # Get or create knowledge state
        state, created = KnowledgeState.objects.get_or_create(
            player=player,
            skill=skill,
            defaults={
                'p_known': 0.3,
                'p_learn': 0.1,
                'p_guess': 0.25,
                'p_slip': 0.1,
                'observations': 0,
            },
        )

        is_correct = result.get('is_correct', False)

        # Run BKT update
        new_p_known = BKTEngine.update(
            p_known=state.p_known,
            p_learn=state.p_learn,
            p_guess=state.p_guess,
            p_slip=state.p_slip,
            is_correct=is_correct,
        )

        state.p_known = new_p_known
        state.observations += 1
        state.save()

        logger.debug(
            "BKT updated: player=%s skill=%s P(K)=%.3f observations=%d",
            player.id, skill, new_p_known, state.observations,
        )

    # ------------------------------------------------------------------
    # Private: challenge stats update
    # ------------------------------------------------------------------

    @classmethod
    def _update_challenge_stats(cls, challenge, result):
        """Update aggregate statistics on the ChallengeParameter.

        Tracks total_attempts, correct_rate, and avg_time for eventual
        IRT recalibration.
        """
        from apps.ai_engine.models import ChallengeParameter
        from apps.ai_engine.algorithms.irt import IRTEngine

        params, created = ChallengeParameter.objects.get_or_create(
            challenge=challenge,
            defaults={
                'discrimination': 1.0,
                'difficulty_b': IRTEngine.initialize_from_difficulty(challenge.difficulty),
                'guessing_c': 0.25 if challenge.challenge_type == 'multiple_choice' else 0.0,
                'total_attempts': 0,
                'correct_rate': 0.5,
                'avg_time_secs': 0.0,
            },
        )

        is_correct = result.get('is_correct', False)
        time_taken = result.get('time_taken_secs', 0)
        old_total = params.total_attempts
        new_total = old_total + 1

        # Running average for correct_rate
        if new_total > 0:
            params.correct_rate = (
                (params.correct_rate * old_total + (1 if is_correct else 0))
                / new_total
            )

        # Running average for avg_time
        if time_taken > 0 and new_total > 0:
            params.avg_time_secs = (
                (params.avg_time_secs * old_total + time_taken) / new_total
            )

        params.total_attempts = new_total
        params.save()

    # ------------------------------------------------------------------
    # Private: session update
    # ------------------------------------------------------------------

    @classmethod
    def _update_session(cls, player, result):
        """Update the most recent active session with challenge data."""
        from apps.ai_engine.models import PlayerSession

        # Find the most recent session that has not ended
        session = PlayerSession.objects.filter(
            player=player,
            ended_at__isnull=True,
        ).order_by('-started_at').first()

        if session is None:
            return

        session.challenges_attempted += 1
        if result.get('is_correct', False):
            session.challenges_correct += 1

        # Update running average response time
        time_taken = result.get('time_taken_secs', 0)
        if time_taken > 0:
            n = session.challenges_attempted
            old_avg = session.avg_response_time
            session.avg_response_time = old_avg + (time_taken - old_avg) / n

            # Welford's online algorithm for variance
            if n > 1:
                delta = time_taken - old_avg
                new_avg = session.avg_response_time
                delta2 = time_taken - new_avg
                session.response_time_variance = (
                    session.response_time_variance * (n - 2) / (n - 1)
                    + delta * delta2 / n
                )

        session.save()

    # ------------------------------------------------------------------
    # Private: recommendation explanation
    # ------------------------------------------------------------------

    @classmethod
    def _explain_recommendation(cls, signals):
        """Generate a human-readable explanation of why a challenge was
        recommended.

        Parameters
        ----------
        signals : dict
            Signal scores from the recommender.

        Returns
        -------
        str
            Natural-language explanation.
        """
        explanations = []

        irt = signals.get('irt', 0)
        bkt = signals.get('bkt', 0)
        fsrs = signals.get('fsrs', 0)
        content = signals.get('content', 0)

        if irt >= 0.7:
            explanations.append("This challenge is at your optimal difficulty level")
        elif irt >= 0.4:
            explanations.append("This challenge offers a good balance of difficulty")

        if bkt >= 0.7:
            explanations.append("it targets one of your knowledge gaps")
        elif bkt >= 0.4:
            explanations.append("it helps develop a skill you're working on")

        if fsrs >= 0.7:
            explanations.append("this topic is due for review based on your memory schedule")
        elif fsrs >= 0.4:
            explanations.append("reviewing this will help reinforce your learning")

        if content >= 0.7:
            explanations.append("it aligns well with your personality profile")

        if not explanations:
            explanations.append("This challenge was selected to introduce variety in your learning")

        # Join with proper punctuation
        result = explanations[0]
        for i, exp in enumerate(explanations[1:], 1):
            if i == len(explanations) - 1:
                result += ", and " + exp
            else:
                result += ", " + exp

        return result + "."
