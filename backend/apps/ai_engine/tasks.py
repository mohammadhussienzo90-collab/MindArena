"""
AI Engine Celery Tasks
=======================
Asynchronous and periodic tasks for the AI engine.

Task schedule (configured in settings via CELERY_BEAT_SCHEDULE):
    - update_engagement_async : on-demand (called after session end)
    - recalibrate_irt_params  : daily at 03:00 UTC
    - generate_learning_paths : daily at 04:00 UTC
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ======================================================================
# On-demand: engagement update
# ======================================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_engagement_async(self, player_id):
    """Asynchronously update engagement score and churn risk for a player.

    This task is dispatched after session end or challenge completion to
    offload the expensive behavioral analytics computation from the
    request-response cycle.

    Parameters
    ----------
    player_id : int
        The player's primary key.
    """
    try:
        from apps.accounts.models import Player
        from apps.ai_engine.algorithms.behavior import BehaviorEngine
        from apps.ai_engine.models import PlayerEngagement, PlayerSession

        player = Player.objects.get(id=player_id)
        now = timezone.now()

        # Compute engagement and churn
        engagement_score = BehaviorEngine.calculate_engagement_score(player)
        churn_risk = BehaviorEngine.predict_churn(player)
        player_type = BehaviorEngine.classify_player_type(player)

        # Get or create engagement record
        engagement, created = PlayerEngagement.objects.get_or_create(
            player=player,
            defaults={
                'engagement_score': engagement_score,
                'churn_risk': churn_risk,
                'personality_cluster': player_type,
            },
        )

        if not created:
            engagement.engagement_score = engagement_score
            engagement.churn_risk = churn_risk
            engagement.personality_cluster = player_type

            # Update session statistics
            from django.db.models import Avg

            recent_sessions = PlayerSession.objects.filter(
                player=player,
                ended_at__isnull=False,
                started_at__gte=now - timedelta(days=30),
            )

            avg_len = recent_sessions.aggregate(
                avg=Avg('duration_secs')
            )['avg'] or 0
            engagement.avg_session_length_secs = avg_len

            week_sessions = recent_sessions.filter(
                started_at__gte=now - timedelta(days=7),
            ).count()
            engagement.sessions_per_week = week_sessions

            # Determine preferred time of day
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
                engagement.preferred_time_of_day = max(
                    hour_counts, key=hour_counts.get
                )

            # Compute optimal session length
            # Based on the session length that produced the best flow scores
            best_sessions = (
                PlayerSession.objects.filter(
                    player=player,
                    ended_at__isnull=False,
                    flow_score__gte=0.5,
                    started_at__gte=now - timedelta(days=60),
                )
                .values_list('duration_secs', flat=True)
            )
            if best_sessions:
                engagement.optimal_session_length = (
                    sum(best_sessions) / len(best_sessions)
                )

            engagement.save()

        logger.info(
            "Engagement updated for player %s: score=%.3f churn=%.3f type=%s",
            player_id, engagement_score, churn_risk, player_type,
        )

    except Exception as exc:
        logger.error(
            "Failed to update engagement for player %s: %s", player_id, exc,
        )
        raise self.retry(exc=exc)


# ======================================================================
# Periodic: IRT recalibration
# ======================================================================

@shared_task
def recalibrate_irt_params():
    """Recalibrate IRT item parameters from accumulated response data.

    For each ChallengeParameter with >= 30 total attempts and that has
    not been calibrated in the last 7 days, run the IRT calibration
    heuristic to update discrimination (a) and difficulty (b).

    This task should be scheduled to run daily (e.g., 03:00 UTC).
    """
    from apps.ai_engine.algorithms.irt import IRTEngine
    from apps.ai_engine.models import ChallengeParameter, PlayerAbility
    from apps.progression.models import PlayerChallengeResult

    now = timezone.now()
    cutoff = now - timedelta(days=7)

    # Find challenges eligible for recalibration
    eligible = ChallengeParameter.objects.filter(
        total_attempts__gte=30,
    ).exclude(
        calibrated_at__gte=cutoff,
    ).select_related('challenge')

    calibrated_count = 0
    skipped_count = 0

    for params in eligible:
        challenge = params.challenge

        # Gather historical responses with theta at time of response
        # We approximate by using current theta for each player
        results = PlayerChallengeResult.objects.filter(
            challenge=challenge,
        ).select_related('player').order_by('-played_at')[:500]

        if len(results) < 10:
            skipped_count += 1
            continue

        # Build (theta, is_correct) tuples
        response_data = []
        for result in results:
            try:
                ability = PlayerAbility.objects.filter(
                    player=result.player,
                    skill=challenge.primary_trait,
                ).first()
                theta = ability.theta if ability else 0.0
            except Exception:
                theta = 0.0

            response_data.append((theta, result.is_correct))

        # Run calibration
        calibration = IRTEngine.calibrate_from_data(response_data)

        if calibration is not None:
            new_a, new_b = calibration

            # Apply smoothing: blend old and new parameters
            # (70% new, 30% old to prevent sudden jumps)
            params.discrimination = 0.7 * new_a + 0.3 * params.discrimination
            params.difficulty_b = 0.7 * new_b + 0.3 * params.difficulty_b

            # Clamp to reasonable ranges
            params.discrimination = max(0.2, min(3.0, params.discrimination))
            params.difficulty_b = max(-3.0, min(3.0, params.difficulty_b))

            params.calibrated_at = now
            params.save()
            calibrated_count += 1
        else:
            skipped_count += 1

    logger.info(
        "IRT recalibration complete: %d calibrated, %d skipped",
        calibrated_count, skipped_count,
    )

    return {
        'calibrated': calibrated_count,
        'skipped': skipped_count,
    }


# ======================================================================
# Periodic: learning path generation
# ======================================================================

@shared_task
def generate_learning_paths():
    """Regenerate learning paths for all active players.

    An "active" player is one who has been active in the last 14 days.
    This task should be scheduled to run daily (e.g., 04:00 UTC).
    """
    from apps.accounts.models import Player
    from apps.ai_engine.algorithms.learning_path import generate_learning_path
    from apps.ai_engine.models import LearningPath

    now = timezone.now()
    active_cutoff = now - timedelta(days=14)

    active_players = Player.objects.filter(
        last_active_at__gte=active_cutoff,
    )

    updated_count = 0
    error_count = 0

    for player in active_players.iterator():
        try:
            path = generate_learning_path(player)

            if not path:
                continue

            lp, created = LearningPath.objects.get_or_create(
                player=player,
                defaults={
                    'current_focus_skill': path[0]['skill'],
                    'skill_sequence': [step['skill'] for step in path],
                    'next_challenges': [],
                },
            )

            if not created:
                lp.current_focus_skill = path[0]['skill']
                lp.skill_sequence = [step['skill'] for step in path]
                lp.path_version += 1
                lp.save()

            # Try to set the focus realm from the first skill's associated realm
            if path[0].get('skill'):
                from apps.realms.models import Realm
                focus_realm = Realm.objects.filter(
                    primary_trait=path[0]['skill'],
                    is_active=True,
                ).first()
                if focus_realm:
                    lp.current_focus_realm = focus_realm
                    lp.save()

            updated_count += 1

        except Exception as e:
            logger.error(
                "Failed to generate learning path for player %s: %s",
                player.id, e,
            )
            error_count += 1

    logger.info(
        "Learning path generation complete: %d updated, %d errors (of %d active players)",
        updated_count, error_count, active_players.count(),
    )

    return {
        'updated': updated_count,
        'errors': error_count,
        'total_active': active_players.count(),
    }


# ======================================================================
# Periodic: nightly AI learning & prompt evolution
# ======================================================================

@shared_task
def nightly_ai_learning():
    """Aggregate player interaction patterns and evolve AI strategies.

    Runs nightly to:
    1. Evaluate companion conversation effectiveness (did players improve?)
    2. Update prompt variant scores based on 24h outcome data
    3. Deactivate consistently underperforming prompt strategies
    4. Generate challenges for active players with identified gaps

    This task should be scheduled to run daily (e.g., 05:00 UTC).
    """
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    results = {
        'companion_evaluations': 0,
        'variants_updated': 0,
        'variants_deactivated': 0,
        'challenges_generated': 0,
    }

    # ---- 1. Evaluate companion conversations from last 24h ----
    try:
        from apps.companion.models import CompanionConversation, CompanionMessage
        from apps.progression.models import PlayerChallengeResult

        recent_convos = CompanionConversation.objects.filter(
            started_at__gte=yesterday,
        ).select_related('player')

        for convo in recent_convos.iterator():
            player = convo.player

            # Check if the player performed better AFTER chatting with Noor
            # (challenges completed in the 4 hours after conversation)
            convo_end = convo.messages.order_by('-created_at').first()
            if not convo_end:
                continue
            after_start = convo_end.created_at
            after_end = after_start + timedelta(hours=4)

            post_chat_results = PlayerChallengeResult.objects.filter(
                player=player,
                played_at__gte=after_start,
                played_at__lte=after_end,
            )

            if post_chat_results.exists():
                accuracy = post_chat_results.filter(
                    is_correct=True,
                ).count() / post_chat_results.count()
                was_positive = accuracy >= 0.5 or post_chat_results.count() >= 2
            else:
                # Player didn't continue playing — neutral (not negative)
                was_positive = False

            results['companion_evaluations'] += 1

    except Exception as e:
        logger.error("Companion evaluation failed: %s", e)

    # ---- 2. Deactivate underperforming prompt variants ----
    try:
        from apps.ai_engine.prompt_evolution import PromptEvolution
        deactivated = PromptEvolution.deactivate_underperformers(
            min_trials=50, min_rate=0.3,
        )
        results['variants_deactivated'] = deactivated
    except Exception as e:
        logger.error("Prompt evolution update failed: %s", e)

    # ---- 3. Generate challenges for active players with gaps ----
    try:
        from apps.accounts.models import Player
        from apps.ai_engine.challenge_generator import ChallengeGenerator

        # Only generate for players who were active in last 3 days
        active_cutoff = now - timedelta(days=3)
        active_players = Player.objects.filter(
            last_active_at__gte=active_cutoff,
        )[:20]  # Limit to 20 players per night to manage API costs

        for player in active_players:
            # Find their weakest realm
            from apps.ai_engine.models import KnowledgeState
            weakest = KnowledgeState.objects.filter(
                player=player,
            ).order_by('p_known').first()

            if weakest and weakest.p_known < 0.7:
                # Find which realm this skill belongs to
                from apps.realms.models import Realm
                realm = Realm.objects.filter(
                    primary_trait=weakest.skill,
                    is_active=True,
                ).first()

                if realm:
                    generated = ChallengeGenerator.generate_for_player(
                        player, realm.slug, count=2,
                    )
                    if generated:
                        results['challenges_generated'] += len(generated)

    except Exception as e:
        logger.error("Challenge generation in nightly task failed: %s", e)

    logger.info("Nightly AI learning complete: %s", results)
    return results
