"""XP, leveling, streaks, and visual stage progression."""
import math
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


class XPService:
    XP_EXPONENT = getattr(settings, 'XP_CURVE_EXPONENT', 1.5)

    @classmethod
    def xp_for_level(cls, level):
        """XP needed to reach a given level."""
        return int(math.floor(100 * (level ** cls.XP_EXPONENT)))

    @classmethod
    def level_from_xp(cls, total_xp):
        """Calculate level from total XP."""
        level = 1
        while cls.xp_for_level(level + 1) <= total_xp:
            level += 1
        return level

    @classmethod
    def award_xp(cls, player, amount, source, source_id=None, realm=None):
        """Award XP to a player, update levels, realm stats."""
        from .models import XPTransaction

        XPTransaction.objects.create(
            player=player,
            amount=amount,
            source=source,
            source_id=source_id,
            realm=realm,
        )

        player.total_xp += amount
        new_level = cls.level_from_xp(player.total_xp)
        leveled_up = new_level > player.overall_level
        player.overall_level = new_level
        player.save(update_fields=['total_xp', 'overall_level'])

        if realm:
            cls.update_realm_stat(player, realm, amount)

        cls.update_streak(player)

        if leveled_up:
            from apps.notifications.services import NotificationService
            NotificationService.send_level_up(player, new_level)

        return {
            'xp_earned': amount,
            'total_xp': player.total_xp,
            'level': player.overall_level,
            'leveled_up': leveled_up,
        }

    @classmethod
    def update_realm_stat(cls, player, realm, xp_amount):
        from .models import PlayerRealmStat
        stat, _ = PlayerRealmStat.objects.get_or_create(
            player=player, realm=realm,
        )
        stat.realm_xp += xp_amount
        stat.realm_level = cls.level_from_xp(stat.realm_xp)
        stat.visual_stage = cls.calculate_visual_stage(stat.realm_level)
        stat.save()
        return stat

    @classmethod
    def calculate_visual_stage(cls, realm_level):
        """0-5 visual transformation based on realm level."""
        if realm_level < 3:
            return 0
        elif realm_level < 6:
            return 1
        elif realm_level < 10:
            return 2
        elif realm_level < 15:
            return 3
        elif realm_level < 20:
            return 4
        return 5

    @classmethod
    def update_streak(cls, player):
        from .models import DailyStreak
        streak, _ = DailyStreak.objects.get_or_create(player=player)
        today = timezone.now().date()

        if streak.last_active_date == today:
            return streak

        if streak.last_active_date == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_active_date = today
        streak.save()
        return streak
