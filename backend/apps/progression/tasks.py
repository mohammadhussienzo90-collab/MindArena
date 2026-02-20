"""Celery async tasks for progression system."""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def check_achievements_async(self, player_id, event_type):
    """Check and award achievements asynchronously after game events."""
    try:
        from apps.accounts.models import Player
        from apps.progression.achievement_checker import AchievementChecker

        player = Player.objects.get(id=player_id)
        new_achievements = AchievementChecker.check_specific(player, event_type)
        slugs = [a['slug'] for a in new_achievements]
        if slugs:
            logger.info(
                "Player %s earned achievements: %s",
                player.display_name, ', '.join(slugs),
            )
        return slugs
    except Exception as exc:
        logger.error("Achievement check failed for player %d: %s", player_id, exc)
        raise self.retry(exc=exc)


@shared_task
def update_daily_streak_async(player_id):
    """Update player's daily streak (called after any activity)."""
    from apps.accounts.models import Player
    from apps.progression.services import XPService

    try:
        player = Player.objects.get(id=player_id)
        streak = XPService.update_streak(player)
        return {
            'player_id': player_id,
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
        }
    except Exception as exc:
        logger.error("Streak update failed for player %d: %s", player_id, exc)
        return None


@shared_task
def recalculate_realm_levels(player_id):
    """Recalculate all realm levels and visual stages for a player."""
    from apps.accounts.models import Player
    from apps.progression.models import PlayerRealmStat
    from apps.progression.services import XPService

    try:
        player = Player.objects.get(id=player_id)
        stats = PlayerRealmStat.objects.filter(player=player)
        updated = 0
        for stat in stats:
            new_level = XPService.level_from_xp(stat.realm_xp)
            new_stage = XPService.calculate_visual_stage(new_level)
            if stat.realm_level != new_level or stat.visual_stage != new_stage:
                stat.realm_level = new_level
                stat.visual_stage = new_stage
                stat.save(update_fields=['realm_level', 'visual_stage'])
                updated += 1

        # Recalculate overall level
        new_overall = XPService.level_from_xp(player.total_xp)
        if player.overall_level != new_overall:
            player.overall_level = new_overall
            player.save(update_fields=['overall_level'])

        logger.info("Recalculated %d realm stats for player %d", updated, player_id)
        return {'player_id': player_id, 'realms_updated': updated}
    except Exception as exc:
        logger.error("Realm recalculation failed for player %d: %s", player_id, exc)
        return None


@shared_task
def cleanup_expired_tokens():
    """Periodic: clean up expired/blacklisted JWT tokens older than 30 days."""
    from datetime import timedelta
    from django.utils import timezone

    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken, OutstandingToken,
        )
        cutoff = timezone.now() - timedelta(days=30)
        # Delete blacklisted tokens whose outstanding token expired before cutoff
        old_blacklisted = BlacklistedToken.objects.filter(
            token__expires_at__lt=cutoff,
        )
        count = old_blacklisted.count()
        old_blacklisted.delete()

        # Delete outstanding tokens that expired before cutoff and aren't blacklisted
        old_outstanding = OutstandingToken.objects.filter(
            expires_at__lt=cutoff,
        )
        outstanding_count = old_outstanding.count()
        old_outstanding.delete()

        logger.info(
            "Token cleanup: removed %d blacklisted, %d outstanding tokens",
            count, outstanding_count,
        )
        return {'blacklisted_removed': count, 'outstanding_removed': outstanding_count}
    except Exception as exc:
        logger.error("Token cleanup failed: %s", exc)
        return None


@shared_task
def generate_daily_stats():
    """Periodic: log daily activity stats."""
    from datetime import timedelta
    from django.utils import timezone
    from apps.accounts.models import Player
    from apps.progression.models import PlayerChallengeResult, DailyStreak

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    active_today = DailyStreak.objects.filter(last_active_date=today).count()
    challenges_today = PlayerChallengeResult.objects.filter(
        played_at__date=today,
    ).count()
    total_players = Player.objects.count()

    stats = {
        'date': today.isoformat(),
        'active_players': active_today,
        'challenges_completed': challenges_today,
        'total_players': total_players,
    }
    logger.info("Daily stats: %s", stats)
    return stats
