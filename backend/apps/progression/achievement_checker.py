"""Achievement checking and awarding service."""
from django.db.models import Count


class AchievementChecker:
    """Checks and awards achievements based on player stats."""

    # Maps event types to the achievement slugs that should be checked.
    # Slugs must match those in seed_achievements.py exactly.
    EVENT_MAP = {
        'challenge_completed': [
            'challenge-rookie', 'challenge-veteran', 'challenge-master',
            'perfectionist',
            'level-5', 'level-10', 'level-25', 'level-50',
            'realm-level-10', 'realm-level-20',
        ],
        'quest_completed': ['quest-first', 'quest-10'],
        'streak_updated': ['streak-3', 'streak-7', 'streak-30', 'streak-100'],
        'companion_chat': ['first-chat', 'deep-thinker'],
        'level_up': ['level-5', 'level-10', 'level-25', 'level-50'],
        'assessment_complete': ['first-steps'],
        'realm_visited': ['realm-explorer', 'balanced-mind'],
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
                # Send notification
                from apps.notifications.services import NotificationService
                NotificationService.send_achievement(player, achievement)

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
                # Send notification
                from apps.notifications.services import NotificationService
                NotificationService.send_achievement(player, achievement)

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
        min_realm_level = 0
        realm_stats = PlayerRealmStat.objects.filter(player=player)
        realms_visited = realm_stats.count()
        if realm_stats.exists():
            levels = [s.realm_level for s in realm_stats]
            max_realm_level = max(levels)
            if realms_visited >= 8:
                min_realm_level = min(levels)

        quests_completed = PlayerQuestProgress.objects.filter(
            player=player, status='completed',
        ).count()

        companion_messages = CompanionMessage.objects.filter(
            conversation__player=player, role='player',
        ).count()

        # Check if personality assessment is complete
        assessment_complete = player.onboarding_done

        return {
            'challenges_completed': challenge_count,
            'perfect_scores': perfect_count,
            'current_streak': current_streak,
            'overall_level': player.overall_level,
            'max_realm_level': max_realm_level,
            'min_realm_level': min_realm_level,
            'realms_visited': realms_visited,
            'quests_completed': quests_completed,
            'companion_messages': companion_messages,
            'assessment_complete': assessment_complete,
        }

    @classmethod
    def _check_requirement(cls, achievement, stats):
        """Check if a single achievement's requirement is met.

        Uses achievement.slug as lookup key. Slugs must match seed_achievements.py.
        """
        slug = achievement.slug
        val = achievement.requirement_value

        checks = {
            # Onboarding
            'first-steps': stats['assessment_complete'],
            'realm-explorer': stats['realms_visited'] >= 8,
            # Challenge milestones
            'challenge-rookie': stats['challenges_completed'] >= 10,
            'challenge-veteran': stats['challenges_completed'] >= 50,
            'challenge-master': stats['challenges_completed'] >= 200,
            'perfectionist': stats['perfect_scores'] >= 10,
            # Streaks
            'streak-3': stats['current_streak'] >= 3,
            'streak-7': stats['current_streak'] >= 7,
            'streak-30': stats['current_streak'] >= 30,
            'streak-100': stats['current_streak'] >= 100,
            # Levels
            'level-5': stats['overall_level'] >= 5,
            'level-10': stats['overall_level'] >= 10,
            'level-25': stats['overall_level'] >= 25,
            'level-50': stats['overall_level'] >= 50,
            # Realm mastery
            'realm-level-10': stats['max_realm_level'] >= 10,
            'realm-level-20': stats['max_realm_level'] >= 20,
            'balanced-mind': stats['min_realm_level'] >= 5,
            # Quests
            'quest-first': stats['quests_completed'] >= 1,
            'quest-10': stats['quests_completed'] >= 10,
            # Companion
            'first-chat': stats['companion_messages'] >= 1,
            'deep-thinker': stats['companion_messages'] >= 50,
        }

        return checks.get(slug, False)
