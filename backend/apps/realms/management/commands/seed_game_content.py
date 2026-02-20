"""
Management command to seed all game content: realms, quests, challenges, feed items.
Usage: python manage.py seed_game_content [--clear]
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.realms.models import Realm, Quest, Challenge
from apps.feed.models import FeedItem


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
REALMS_FILE = DATA_DIR / "realms_seed.json"
CHALLENGES_DIR = DATA_DIR / "challenges"

# Auto-generate quests from challenge groupings per realm
QUEST_TEMPLATES = {
    "logic_fortress": [
        {"slug": "lf-quest-patterns", "title_en": "Pattern Master", "title_ar": "سيد الأنماط",
         "description_en": "Prove your pattern recognition skills.", "order": 1,
         "challenge_slugs": ["lf-pattern-sequence-1", "lf-pattern-visual-1", "lf-pattern-letter-1"]},
        {"slug": "lf-quest-logic", "title_en": "Logic Champion", "title_ar": "بطل المنطق",
         "description_en": "Conquer logical deduction challenges.", "order": 2,
         "challenge_slugs": ["lf-logic-deduction-1", "lf-logic-puzzle-1", "lf-logic-grid-1"]},
        {"slug": "lf-quest-math", "title_en": "Number Wizard", "title_ar": "ساحر الأرقام",
         "description_en": "Master mathematical reasoning.", "order": 3,
         "challenge_slugs": ["lf-math-logic-1", "lf-math-word-1", "lf-probability-1"]},
        {"slug": "lf-quest-advanced", "title_en": "Fortress Guardian", "title_ar": "حارس القلعة",
         "description_en": "Take on the fortress's toughest challenges.", "order": 4,
         "challenge_slugs": ["lf-spatial-1", "lf-timed-calc-1", "lf-code-breaking-1", "lf-analogy-1", "lf-sequence-1", "lf-oddone-1"]},
    ],
    "emotion_ocean": [
        {"slug": "eo-quest-empathy", "title_en": "Empathy Explorer", "title_ar": "مستكشف التعاطف",
         "description_en": "Develop your empathy and emotional reading skills.", "order": 1,
         "challenge_slugs": ["eo-empathy-scenario-1", "eo-emotion-read-1", "eo-emotion-vocab-1"]},
        {"slug": "eo-quest-self", "title_en": "Inner Navigator", "title_ar": "الملاح الداخلي",
         "description_en": "Deepen your self-awareness and emotional regulation.", "order": 2,
         "challenge_slugs": ["eo-self-awareness-1", "eo-regulation-1", "eo-perspective-1"]},
        {"slug": "eo-quest-connect", "title_en": "Heart Bridge", "title_ar": "جسر القلب",
         "description_en": "Strengthen social-emotional connections.", "order": 3,
         "challenge_slugs": ["eo-social-skill-1", "eo-boundary-1", "eo-emotional-scenario-1", "eo-creative-prompt-1"]},
    ],
    "creativity_nebula": [
        {"slug": "cn-quest-divergent", "title_en": "Divergent Thinker", "title_ar": "المفكر التباعدي",
         "description_en": "Expand your creative thinking abilities.", "order": 1,
         "challenge_slugs": ["cn-creative-prompt-1", "cn-improv-1", "cn-story-build-1"]},
        {"slug": "cn-quest-connections", "title_en": "Connection Finder", "title_ar": "باحث الروابط",
         "description_en": "Find hidden connections between ideas.", "order": 2,
         "challenge_slugs": ["cn-word-association-1", "cn-word-association-2", "cn-connect-dots-1"]},
        {"slug": "cn-quest-innovator", "title_en": "Innovation Lab", "title_ar": "مختبر الابتكار",
         "description_en": "Apply creative thinking to real problems.", "order": 3,
         "challenge_slugs": ["cn-perspective-shift-1", "cn-visual-thinking-1", "cn-metaphor-1", "cn-reverse-thinking-1"]},
    ],
    "discipline_citadel": [
        {"slug": "dc-quest-habits", "title_en": "Habit Builder", "title_ar": "بنّاء العادات",
         "description_en": "Learn the science of building strong habits.", "order": 1,
         "challenge_slugs": ["dc-scenario-1", "dc-mcq-1", "dc-mcq-3"]},
        {"slug": "dc-quest-willpower", "title_en": "Willpower Warrior", "title_ar": "محارب الإرادة",
         "description_en": "Strengthen your self-discipline muscle.", "order": 2,
         "challenge_slugs": ["dc-scenario-2", "dc-mcq-2", "dc-scenario-4", "dc-mcq-4"]},
        {"slug": "dc-quest-goals", "title_en": "Goal Architect", "title_ar": "مهندس الأهداف",
         "description_en": "Design and commit to meaningful goals.", "order": 3,
         "challenge_slugs": ["dc-scenario-3", "dc-creative-1", "dc-creative-2"]},
    ],
    "knowledge_peaks": [
        {"slug": "kp-quest-methods", "title_en": "Study Scientist", "title_ar": "عالم الدراسة",
         "description_en": "Master evidence-based learning techniques.", "order": 1,
         "challenge_slugs": ["kp-mcq-1", "kp-mcq-2", "kp-mcq-4"]},
        {"slug": "kp-quest-critical", "title_en": "Truth Seeker", "title_ar": "باحث الحقيقة",
         "description_en": "Sharpen your critical thinking and information literacy.", "order": 2,
         "challenge_slugs": ["kp-scenario-1", "kp-mcq-3", "kp-scenario-2"]},
        {"slug": "kp-quest-growth", "title_en": "Lifelong Learner", "title_ar": "المتعلم مدى الحياة",
         "description_en": "Embrace growth mindset and self-directed learning.", "order": 3,
         "challenge_slugs": ["kp-scenario-3", "kp-mcq-5", "kp-creative-1", "kp-creative-2"]},
    ],
    "social_bridge": [
        {"slug": "sb-quest-listen", "title_en": "Active Listener", "title_ar": "المستمع الفعال",
         "description_en": "Master the art of truly hearing others.", "order": 1,
         "challenge_slugs": ["sb-mcq-1", "sb-mcq-2", "sb-mcq-4"]},
        {"slug": "sb-quest-conflict", "title_en": "Peace Builder", "title_ar": "بنّاء السلام",
         "description_en": "Navigate conflicts with grace and skill.", "order": 2,
         "challenge_slugs": ["sb-scenario-1", "sb-scenario-3", "sb-mcq-3", "sb-creative-2"]},
        {"slug": "sb-quest-lead", "title_en": "Team Leader", "title_ar": "قائد الفريق",
         "description_en": "Lead and inspire others effectively.", "order": 3,
         "challenge_slugs": ["sb-scenario-2", "sb-scenario-4", "sb-creative-1"]},
    ],
    "wealth_garden": [
        {"slug": "wg-quest-basics", "title_en": "Money Foundations", "title_ar": "أساسيات المال",
         "description_en": "Learn the building blocks of financial literacy.", "order": 1,
         "challenge_slugs": ["wg-mcq-1", "wg-mcq-4", "wg-mcq-3"]},
        {"slug": "wg-quest-smart", "title_en": "Smart Spender", "title_ar": "المنفق الذكي",
         "description_en": "Make wise financial decisions in real life.", "order": 2,
         "challenge_slugs": ["wg-scenario-1", "wg-mcq-2", "wg-scenario-4", "wg-creative-2"]},
        {"slug": "wg-quest-grow", "title_en": "Wealth Builder", "title_ar": "بنّاء الثروة",
         "description_en": "Think entrepreneurially and build long-term wealth.", "order": 3,
         "challenge_slugs": ["wg-scenario-2", "wg-scenario-3", "wg-creative-1"]},
    ],
    "wellness_grove": [
        {"slug": "wv-quest-body", "title_en": "Body Wisdom", "title_ar": "حكمة الجسد",
         "description_en": "Understand your body's needs for peak performance.", "order": 1,
         "challenge_slugs": ["wv-mcq-1", "wv-mcq-3", "wv-mcq-4"]},
        {"slug": "wv-quest-mind", "title_en": "Mind Healer", "title_ar": "معالج العقل",
         "description_en": "Build mental resilience and emotional balance.", "order": 2,
         "challenge_slugs": ["wv-scenario-1", "wv-mcq-2", "wv-scenario-2", "wv-scenario-3"]},
        {"slug": "wv-quest-practice", "title_en": "Wellness Practitioner", "title_ar": "ممارس العافية",
         "description_en": "Create sustainable self-care practices.", "order": 3,
         "challenge_slugs": ["wv-creative-1", "wv-creative-2", "wv-mcq-5"]},
    ],
}

# Feed items seed data
FEED_ITEMS = [
    {"title_en": "The 2-Minute Rule", "body_en": "If a task takes less than 2 minutes, do it now. This simple rule from David Allen's GTD method prevents small tasks from piling up and overwhelming you.",
     "content_type": "tip", "realm_slug": "discipline_citadel", "xp_value": 5},
    {"title_en": "Your Brain on Exercise", "body_en": "A 20-minute walk increases BDNF (brain-derived neurotrophic factor), which literally grows new brain cells. Your next great idea might come during a walk.",
     "content_type": "fact", "realm_slug": "wellness_grove", "xp_value": 5},
    {"title_en": "The Zeigarnik Effect", "body_en": "Your brain remembers incomplete tasks better than completed ones. This is why unfinished work keeps nagging you. Write down your open tasks to free your mind.",
     "content_type": "fact", "realm_slug": "knowledge_peaks", "xp_value": 5},
    {"title_en": "Mirror Neurons", "body_en": "Your brain has 'mirror neurons' that fire both when you perform an action and when you see someone else do it. This is the neurological basis of empathy — you literally feel what others feel.",
     "content_type": "fact", "realm_slug": "emotion_ocean", "xp_value": 5},
    {"title_en": "The 5-4-3-2-1 Grounding", "body_en": "Feeling anxious? Name 5 things you see, 4 you hear, 3 you can touch, 2 you smell, 1 you taste. This sensory technique pulls you out of anxiety spirals and into the present.",
     "content_type": "tip", "realm_slug": "wellness_grove", "xp_value": 5},
    {"title_en": "Pay Yourself First", "body_en": "The #1 wealth-building habit: save before you spend. Transfer money to savings the day you get paid, not at the end of the month. What's left is what you spend.",
     "content_type": "tip", "realm_slug": "wealth_garden", "xp_value": 5},
    {"title_en": "The Rubber Duck Method", "body_en": "Stuck on a problem? Explain it out loud to a rubber duck (or any object). The act of articulating the problem often reveals the solution. Programmers call this 'rubber duck debugging'.",
     "content_type": "tip", "realm_slug": "creativity_nebula", "xp_value": 5},
    {"title_en": "Brené Brown on Vulnerability", "body_en": "\"Vulnerability is not winning or losing; it's having the courage to show up and be seen when we have no control over the outcome.\" — Brené Brown",
     "content_type": "quote", "realm_slug": "social_bridge", "xp_value": 3},
    {"title_en": "The Eisenhower Matrix", "body_en": "Organize tasks by urgency and importance: (1) Urgent+Important: Do now, (2) Important+Not Urgent: Schedule, (3) Urgent+Not Important: Delegate, (4) Neither: Eliminate. Most people live in quadrant 3.",
     "content_type": "tip", "realm_slug": "discipline_citadel", "xp_value": 5},
    {"title_en": "Your Memory Palace", "body_en": "The 'method of loci' — placing items to remember in familiar locations in your mind — has been used since ancient Greece. Memory champions use this technique to memorize thousands of digits.",
     "content_type": "fact", "realm_slug": "knowledge_peaks", "xp_value": 5},
    {"title_en": "Emotional Contagion", "body_en": "Emotions spread like viruses. Research shows that if your friend's friend's friend is happy, you're 6% more likely to be happy too. Your emotional state affects people three degrees out in your social network.",
     "content_type": "fact", "realm_slug": "emotion_ocean", "xp_value": 5},
    {"title_en": "The Rule of 72", "body_en": "Divide 72 by your investment's annual return rate to estimate how many years it takes to double. At 8% return: 72÷8 = 9 years to double your money. Start early!",
     "content_type": "tip", "realm_slug": "wealth_garden", "xp_value": 5},
    {"title_en": "Steve Jobs on Creativity", "body_en": "\"Creativity is just connecting things. When you ask creative people how they did something, they feel a little guilty because they didn't really do it, they just saw something.\" — Steve Jobs",
     "content_type": "quote", "realm_slug": "creativity_nebula", "xp_value": 3},
    {"title_en": "The Benjamin Franklin Effect", "body_en": "Want someone to like you? Ask them for a small favor. Counterintuitively, doing someone a favor makes the doer like the recipient more. Franklin used this to win over political rivals.",
     "content_type": "fact", "realm_slug": "social_bridge", "xp_value": 5},
    {"title_en": "Box Breathing", "body_en": "Navy SEALs use this: Breathe in 4 seconds, hold 4 seconds, out 4 seconds, hold 4 seconds. Repeat 4 times. This activates your parasympathetic nervous system and reduces stress in under 2 minutes.",
     "content_type": "tip", "realm_slug": "wellness_grove", "xp_value": 5},
    {"title_en": "Atomic Habits Key Insight", "body_en": "\"You do not rise to the level of your goals. You fall to the level of your systems.\" — James Clear. Build systems, not just goals.",
     "content_type": "quote", "realm_slug": "discipline_citadel", "xp_value": 3},
    {"title_en": "The Dunbar Number", "body_en": "Anthropologist Robin Dunbar found humans can maintain about 150 stable social relationships. Within that: ~5 intimate, ~15 close, ~50 friends, ~150 acquaintances. Quality over quantity.",
     "content_type": "fact", "realm_slug": "social_bridge", "xp_value": 5},
    {"title_en": "Sleep and Memory", "body_en": "During deep sleep, your brain replays and consolidates the day's learning. Pulling an all-nighter before an exam actually makes you perform WORSE than sleeping normally and studying less.",
     "content_type": "fact", "realm_slug": "knowledge_peaks", "xp_value": 5},
    {"title_en": "The Latte Factor", "body_en": "Small daily expenses add up: $5/day × 365 = $1,825/year. Invested at 8% for 30 years = $206,000. It's not about giving up coffee — it's about being aware of where small amounts go.",
     "content_type": "fact", "realm_slug": "wealth_garden", "xp_value": 5},
    {"title_en": "Salvador Dalí's Creativity Hack", "body_en": "Dalí would nap holding a key over a plate. As he drifted off, he'd drop the key, the clang would wake him, and he'd capture the creative ideas from the hypnagogic state between waking and sleeping.",
     "content_type": "fact", "realm_slug": "creativity_nebula", "xp_value": 5},
]


class Command(BaseCommand):
    help = "Seed all game content: realms, quests, challenges, and feed items."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Clear existing game content before seeding."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing content...")
            FeedItem.objects.all().delete()
            Challenge.objects.all().delete()
            Quest.objects.all().delete()
            Realm.objects.all().delete()
            self.stdout.write(self.style.WARNING("All game content cleared."))

        self._seed_realms()
        self._seed_quests_and_challenges()
        self._seed_feed_items()
        self.stdout.write(self.style.SUCCESS("Game content seeded successfully!"))

    def _seed_realms(self):
        with open(REALMS_FILE, encoding="utf-8") as f:
            realms_data = json.load(f)

        created = 0
        for data in realms_data:
            _, was_created = Realm.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name_en": data["name_en"],
                    "name_ar": data.get("name_ar", ""),
                    "description_en": data["description_en"],
                    "description_ar": data.get("description_ar", ""),
                    "icon": data.get("icon", data["slug"]),
                    "color_primary": data.get("color_primary", "#333333"),
                    "color_secondary": data.get("color_secondary", "#666666"),
                    "unlock_level": data.get("unlock_level", 1),
                    "sort_order": data.get("sort_order", 0),
                    "primary_trait": data.get("primary_trait", ""),
                    "secondary_trait": data.get("secondary_trait", ""),
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Realms: {created} created, {len(realms_data) - created} updated.")

    def _seed_quests_and_challenges(self):
        realms = {r.slug: r for r in Realm.objects.all()}
        quest_count = 0
        challenge_count = 0

        for realm_slug, quests in QUEST_TEMPLATES.items():
            realm = realms.get(realm_slug)
            if not realm:
                self.stdout.write(self.style.WARNING(f"  Realm '{realm_slug}' not found, skipping."))
                continue

            # Load challenges for this realm
            challenge_file = CHALLENGES_DIR / f"{realm_slug}.json"
            if not challenge_file.exists():
                self.stdout.write(self.style.WARNING(f"  No challenges file for '{realm_slug}'."))
                continue

            with open(challenge_file, encoding="utf-8") as f:
                challenges_data = json.load(f)

            # Index challenges by slug
            challenges_by_slug = {c["slug"]: c for c in challenges_data}

            for quest_data in quests:
                quest, was_created = Quest.objects.update_or_create(
                    slug=quest_data["slug"],
                    defaults={
                        "realm": realm,
                        "title_en": quest_data["title_en"],
                        "title_ar": quest_data["title_ar"],
                        "description_en": quest_data["description_en"],
                        "sort_order": quest_data["order"],
                        "is_active": True,
                    },
                )
                if was_created:
                    quest_count += 1

                # Seed challenges for this quest
                for order, c_slug in enumerate(quest_data["challenge_slugs"], 1):
                    c_data = challenges_by_slug.get(c_slug)
                    if not c_data:
                        self.stdout.write(self.style.WARNING(
                            f"  Challenge '{c_slug}' not found in data file."
                        ))
                        continue

                    _, c_created = Challenge.objects.update_or_create(
                        slug=c_data["slug"],
                        defaults={
                            "quest": quest,
                            "challenge_type": c_data["challenge_type"],
                            "title_en": c_data["title_en"],
                            "title_ar": c_data.get("title_ar", ""),
                            "description_en": c_data.get("description_en", ""),
                            "difficulty": c_data["difficulty"],
                            "primary_trait": c_data.get("primary_trait", ""),
                            "base_xp": c_data["base_xp"],
                            "bonus_xp": c_data["bonus_xp"],
                            "time_limit_secs": c_data.get("time_limit_secs"),
                            "content": c_data["content"],
                            "sort_order": order,
                            "is_active": True,
                        },
                    )
                    if c_created:
                        challenge_count += 1

        self.stdout.write(f"  Quests: {quest_count} created. Challenges: {challenge_count} created.")

    def _seed_feed_items(self):
        realms = {r.slug: r for r in Realm.objects.all()}
        created = 0

        for i, item in enumerate(FEED_ITEMS):
            realm = realms.get(item["realm_slug"])
            slug = f"feed-{item['content_type']}-{i+1:03d}"
            _, was_created = FeedItem.objects.update_or_create(
                slug=slug,
                defaults={
                    "title_en": item["title_en"],
                    "body_en": item["body_en"],
                    "content_type": item["content_type"],
                    "realm": realm,
                    "xp_value": item["xp_value"],
                    "is_active": True,
                    "is_premium": False,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Feed items: {created} created, {len(FEED_ITEMS) - created} updated.")
