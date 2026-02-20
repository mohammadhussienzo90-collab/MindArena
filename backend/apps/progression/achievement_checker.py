"""Achievement checking and awarding service."""
from django.db.models import Count


class AchievementChecker:
    """Checks and awards achievements based on player stats."""

    # Maps requirement_type to a callable that returns the player's current value
    EVENT_MAP = {
        'challenge_completed': [
            'first_challenge', 'challenges_10', 'challenges_50', 'challenges_100',
            'perfect_10', 'level_5', 'level_10', 'level_25', 'level_50',
            'realm_master',
        ],
        'quest_completed': ['quest_first', 'quests_10'],
        'streak_updated': ['streak_3', 'streak_7', 'streak_30'],
        'companion_chat': ['companion_first', 'companion_100'],
        'level_up': ['level_5', 'level_10', 'level_25', 'level_50'],
    }

    @classmethod
    def check_and_award(cls, player):
        """Check all achievements and award any newly earned ones."""
        from .models import Achievement, PlayerAchievement

        earned_slugs = set(
            PlayerAchievement.objects.filter(player=player)
            .values_list('achievement__slug', flat=True)
        )

        unearned = Achievement.objects.exclude(slug__in=earned_slugs)
        if not unearned.exists():
            return []

        stats = cls._get_player_stats(player)
        newly_earned = []

        for achievement in unearned:
            if cls._check_requirement(achievement, stats):
                PlayerAchievement.objects.create(
                    player=player, achievement=achievement,
                )
                newly_earned.append({
                    'slug': achievement.slug,
                    'title_en': achievement.title_en,
                    'category': achievement.category,
                    'xp_reward': achievement.xp_reward,
                    'icon': achievement.icon,
                })
                # Award achievement XP
                if achievement.xp_reward > 0:
                    from .services import XPService
                    XPService.award_xp(
                        player=player,
                        amount=achievement.xp_reward,
                        source='achievement',
                        source_id=achievement.id,
                    )

        return newly_earned

    @classmethod
    def check_specific(cls, player, event_type):
        """Check only achievements relevant to a specific event type."""
        from .models import Achievement, PlayerAchievement

        relevant_types = cls.EVENT_MAP.get(event_type, [])
        if not relevant_types:
            return []

        earned_slugs = set(
            PlayerAchievement.objects.filter(player=player)
            .values_list('achievement__slug', flat=True)
        )

        unearned = Achievement.objects.filter(
            slug__in=relevant_types,
        ).exclude(slug__in=earned_slugs)

        if not unearned.exists():
            return []

        stats = cls._get_player_stats(player)
        newly_earned = []

        for achievement in unearned:
            if cls._check_requirement(achievement, stats):
                PlayerAchievement.objects.create(
                    player=player, achievement=achievement,
                )
                newly_earned.append({
                    'slug': achievement.slug,
                    'title_en': achievement.title_en,
                    'category': achievement.category,
                    'xp_reward': achievement.xp_reward,
                    'icon': achievement.icon,
                })
                if achievement.xp_reward > 0:
                    from .services import XPService
                    XPService.award_xp(
                        player=player,
                        amount=achievement.xp_reward,
                        source='achievement',
                        source_id=achievement.id,
                    )

        return newly_earned

    @classmethod
    def _get_player_stats(cls, player):
        """Gather all player stats needed for achievement checks."""
        from .models import (
            PlayerChallengeResult, DailyStreak,
            PlayerRealmStat, PlayerQuestProgress,
        )
        from apps.companion.models import CompanionMessage

        challenge_count = PlayerChallengeResult.objects.filter(
            player=player, is_correct=True,
        ).count()

        perfect_count = PlayerChallengeResult.objects.filter(
            player=player, score=100,
        ).count()

        streak = DailyStreak.objects.filter(player=player).first()
        current_streak = streak.current_streak if streak else 0

        max_realm_level = 0
        realm_stats = PlayerRealmStat.objects.filter(player=player)
        if realm_stats.exists():
            max_realm_level = max(s.realm_level for s in realm_stats)

        quests_completed = PlayerQuestProgress.objects.filter(
            player=player, status='completed',
        ).count()

        companion_messages = CompanionMessage.objects.filter(
            conversation__player=player, role='player',
        ).count()

        return {
            'challenges_completed': challenge_count,
            'perfect_scores': perfect_count,
            'current_streak': current_streak,
            'overall_level': player.overall_level,
            'max_realm_level': max_realm_level,
            'quests_completed': quests_completed,
            'companion_messages': companion_messages,
        }

    @classmethod
    def _check_requirement(cls, achievement, stats):
        """Check if a single achievement's requirement is met."""
        req_type = achievement.slug
        req_value = achievement.requirement_value

        checks = {
            'first_challenge': stats['challenges_completed'] >= 1,
            'challenges_10': stats['challenges_completed'] >= 10,
            'challenges_50': stats['challenges_completed'] >= 50,
            'challenges_100': stats['challenges_completed'] >= 100,
            'perfect_10': stats['perfect_scores'] >= 10,
            'streak_3': stats['current_streak'] >= 3,
            'streak_7': stats['current_streak'] >= 7,
            'streak_30': stats['current_streak'] >= 30,
            'level_5': stats['overall_level'] >= 5,
            'level_10': stats['overall_level'] >= 10,
            'level_25': stats['overall_level'] >= 25,
            'level_50': stats['overall_level'] >= 50,
            'realm_master': stats['max_realm_level'] >= 25,
            'quest_first': stats['quests_completed'] >= 1,
            'quests_10': stats['quests_completed'] >= 10,
            'companion_first': stats['companion_messages'] >= 1,
            'companion_100': stats['companion_messages'] >= 100,
        }

        return checks.get(req_type, False)
