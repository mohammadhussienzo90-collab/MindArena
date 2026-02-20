"""Seed achievements for MindArena."""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.progression.models import Achievement


ACHIEVEMENTS = [
    # === Onboarding ===
    {"slug": "first-steps", "title_en": "First Steps", "title_ar": "الخطوات الأولى",
     "description_en": "Complete the personality assessment.", "category": "onboarding",
     "requirement_type": "assessment_complete", "requirement_value": 1, "xp_reward": 50, "icon": "flag"},

    {"slug": "realm-explorer", "title_en": "Realm Explorer", "title_ar": "مستكشف العوالم",
     "description_en": "Visit all 8 realms.", "category": "onboarding",
     "requirement_type": "realms_visited", "requirement_value": 8, "xp_reward": 100, "icon": "compass"},

    # === Challenge Milestones ===
    {"slug": "challenge-rookie", "title_en": "Challenge Rookie", "title_ar": "مبتدئ التحديات",
     "description_en": "Complete 10 challenges.", "category": "challenges",
     "requirement_type": "challenges_completed", "requirement_value": 10, "xp_reward": 50, "icon": "star"},

    {"slug": "challenge-veteran", "title_en": "Challenge Veteran", "title_ar": "محترف التحديات",
     "description_en": "Complete 50 challenges.", "category": "challenges",
     "requirement_type": "challenges_completed", "requirement_value": 50, "xp_reward": 150, "icon": "medal"},

    {"slug": "challenge-master", "title_en": "Challenge Master", "title_ar": "سيد التحديات",
     "description_en": "Complete 200 challenges.", "category": "challenges",
     "requirement_type": "challenges_completed", "requirement_value": 200, "xp_reward": 500, "icon": "trophy"},

    {"slug": "perfectionist", "title_en": "Perfectionist", "title_ar": "الكمالي",
     "description_en": "Get a perfect score on 10 challenges.", "category": "challenges",
     "requirement_type": "perfect_challenges", "requirement_value": 10, "xp_reward": 200, "icon": "diamond"},

    # === Streak Achievements ===
    {"slug": "streak-3", "title_en": "Getting Started", "title_ar": "بداية الطريق",
     "description_en": "Maintain a 3-day streak.", "category": "streaks",
     "requirement_type": "streak_days", "requirement_value": 3, "xp_reward": 30, "icon": "flame"},

    {"slug": "streak-7", "title_en": "Week Warrior", "title_ar": "محارب الأسبوع",
     "description_en": "Maintain a 7-day streak.", "category": "streaks",
     "requirement_type": "streak_days", "requirement_value": 7, "xp_reward": 75, "icon": "flame"},

    {"slug": "streak-30", "title_en": "Monthly Master", "title_ar": "سيد الشهر",
     "description_en": "Maintain a 30-day streak.", "category": "streaks",
     "requirement_type": "streak_days", "requirement_value": 30, "xp_reward": 300, "icon": "fire"},

    {"slug": "streak-100", "title_en": "Centurion", "title_ar": "المئوي",
     "description_en": "Maintain a 100-day streak.", "category": "streaks",
     "requirement_type": "streak_days", "requirement_value": 100, "xp_reward": 1000, "icon": "crown", "is_hidden": True},

    # === Level Achievements ===
    {"slug": "level-5", "title_en": "Rising Star", "title_ar": "نجم صاعد",
     "description_en": "Reach level 5.", "category": "levels",
     "requirement_type": "player_level", "requirement_value": 5, "xp_reward": 50, "icon": "arrow-up"},

    {"slug": "level-10", "title_en": "Double Digits", "title_ar": "الأرقام المزدوجة",
     "description_en": "Reach level 10.", "category": "levels",
     "requirement_type": "player_level", "requirement_value": 10, "xp_reward": 100, "icon": "zap"},

    {"slug": "level-25", "title_en": "Quarter Century", "title_ar": "ربع قرن",
     "description_en": "Reach level 25.", "category": "levels",
     "requirement_type": "player_level", "requirement_value": 25, "xp_reward": 250, "icon": "shield"},

    {"slug": "level-50", "title_en": "Legendary", "title_ar": "أسطوري",
     "description_en": "Reach level 50.", "category": "levels",
     "requirement_type": "player_level", "requirement_value": 50, "xp_reward": 500, "icon": "crown", "is_hidden": True},

    # === Realm Mastery ===
    {"slug": "realm-level-10", "title_en": "Realm Specialist", "title_ar": "متخصص العالم",
     "description_en": "Reach level 10 in any realm.", "category": "realm_mastery",
     "requirement_type": "realm_level", "requirement_value": 10, "xp_reward": 150, "icon": "target"},

    {"slug": "realm-level-20", "title_en": "Realm Master", "title_ar": "سيد العالم",
     "description_en": "Reach level 20 in any realm.", "category": "realm_mastery",
     "requirement_type": "realm_level", "requirement_value": 20, "xp_reward": 400, "icon": "award"},

    {"slug": "balanced-mind", "title_en": "Balanced Mind", "title_ar": "عقل متوازن",
     "description_en": "Reach level 5 in all 8 realms.", "category": "realm_mastery",
     "requirement_type": "all_realms_level", "requirement_value": 5, "xp_reward": 500, "icon": "balance"},

    # === Quest Achievements ===
    {"slug": "quest-first", "title_en": "Quest Starter", "title_ar": "بادئ المهام",
     "description_en": "Complete your first quest.", "category": "quests",
     "requirement_type": "quests_completed", "requirement_value": 1, "xp_reward": 50, "icon": "scroll"},

    {"slug": "quest-10", "title_en": "Questionnaire", "title_ar": "محقق المهام",
     "description_en": "Complete 10 quests.", "category": "quests",
     "requirement_type": "quests_completed", "requirement_value": 10, "xp_reward": 200, "icon": "book"},

    # === Social / Companion ===
    {"slug": "first-chat", "title_en": "Hello Noor", "title_ar": "مرحباً نور",
     "description_en": "Have your first conversation with Noor.", "category": "companion",
     "requirement_type": "companion_chats", "requirement_value": 1, "xp_reward": 25, "icon": "message"},

    {"slug": "deep-thinker", "title_en": "Deep Thinker", "title_ar": "المفكر العميق",
     "description_en": "Have 50 conversations with Noor.", "category": "companion",
     "requirement_type": "companion_chats", "requirement_value": 50, "xp_reward": 200, "icon": "brain"},
]


class Command(BaseCommand):
    help = "Seed achievements for MindArena."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing achievements before seeding.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            Achievement.objects.all().delete()
            self.stdout.write(self.style.WARNING("Achievements cleared."))

        created = 0
        for data in ACHIEVEMENTS:
            _, was_created = Achievement.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "title_en": data["title_en"],
                    "title_ar": data.get("title_ar", ""),
                    "description_en": data["description_en"],
                    "icon": data.get("icon", ""),
                    "category": data["category"],
                    "requirement_type": data["requirement_type"],
                    "requirement_value": data["requirement_value"],
                    "xp_reward": data["xp_reward"],
                    "is_hidden": data.get("is_hidden", False),
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Achievements: {created} created, {len(ACHIEVEMENTS) - created} updated."
        ))
