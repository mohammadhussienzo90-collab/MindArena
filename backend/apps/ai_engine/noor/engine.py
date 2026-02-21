"""
Smart Noor Engine
==================
Main engine for the Smart Noor AI companion. Generates contextual, personality-
aware responses using template selection and Markov-style variation -- all
without any external API calls.

Architecture
------------
1. **Intent Classification** -- keyword-based intent detection.
2. **Player Context** -- personality, streak, realm stats, engagement.
3. **Emotion Inference** -- text + behavior signals (EmotionEngine).
4. **Coaching Strategy** -- adaptive strategy selection (CoachingStrategy).
5. **Template Selection** -- personality-filtered, category-aware selection.
6. **Markov Variation** -- lightweight natural language variation for freshness.

Usage
-----
::

    from apps.ai_engine.noor.engine import SmartNoorEngine

    response = SmartNoorEngine.generate_response(
        player=player,
        message="I'm stuck on this logic challenge!",
        context={'realm': 'logic_fortress'},
    )
    # response = {
    #     'text': 'Hey Ahmed, I know...',
    #     'emotion': 'frustrated',
    #     'emotion_confidence': 0.7,
    #     'strategy': 'growth_mindset',
    #     'intent': 'help',
    #     'category': 'frustration_support',
    #     'suggestions': [...],
    # }
"""

import hashlib
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from .coaching import CoachingStrategy
from .emotion import EmotionEngine
from .templates import (
    TEMPLATES,
    fill_template,
    filter_by_personality,
    get_realm_templates,
)


class SmartNoorEngine:
    """Template-based AI companion engine that works without external APIs."""

    # ------------------------------------------------------------------ #
    # Intent keywords
    # ------------------------------------------------------------------ #
    INTENT_KEYWORDS = {
        'help': [
            'help', 'stuck', 'how do i', 'what should', 'confused',
            'dont know', "don't know", 'need help', 'assist', 'guide',
            'hint', 'how to', 'tip', 'explain', 'teach',
        ],
        'greeting': [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon',
            'good evening', 'good night', 'salam', 'marhaba', 'ahlan',
            'hola', 'sup', 'yo', 'greetings', 'howdy',
            # Arabic greetings
            '\u0645\u0631\u062d\u0628\u0627',  # marhaba
            '\u0627\u0647\u0644\u0627',          # ahlan
            '\u0627\u0644\u0633\u0644\u0627\u0645',  # al-salam
        ],
        'feeling': [
            'feel', 'feeling', 'sad', 'happy', 'angry', 'anxious',
            'stressed', 'tired', 'lonely', 'frustrated', 'excited',
            'depressed', 'worried', 'scared', 'nervous', 'overwhelmed',
            'proud', 'grateful',
        ],
        'progress': [
            'progress', 'how am i', 'level', 'xp', 'stats', 'streak',
            'score', 'performance', 'how did i', 'status', 'rank',
            'standing', 'my stats', 'improvement', 'growth',
        ],
        'motivation': [
            'motivated', 'motivation', 'give up', 'hard', 'difficult',
            'quit', 'bored', 'pointless', 'why bother', 'not worth',
            'no point', 'lost hope', 'uninspired', 'burned out',
        ],
        'realm': [
            'realm', 'logic', 'emotion', 'creativity', 'discipline',
            'knowledge', 'social', 'wealth', 'wellness', 'fortress',
            'ocean', 'nebula', 'citadel', 'peaks', 'bridge', 'garden',
            'grove',
        ],
        'challenge': [
            'challenge', 'quest', 'puzzle', 'answer', 'hint',
            'question', 'problem', 'exercise', 'task', 'test',
            'wrong answer', 'correct', 'solution', 'solve',
        ],
        'goal': [
            'goal', 'plan', 'want to', 'improve', 'better at',
            'target', 'aim', 'objective', 'resolution', 'aspire',
            'dream', 'milestone', 'ambition', 'next step',
        ],
    }

    # Intent -> template category mapping
    INTENT_CATEGORY_MAP = {
        'help': 'challenge_help',
        'greeting': 'greeting',
        'feeling': None,  # Determined by emotion
        'progress': 'encouragement',
        'motivation': None,  # Determined by emotion
        'realm': 'realm_specific',
        'challenge': 'challenge_help',
        'goal': 'goal_setting',
    }

    # Emotion -> template category mapping
    EMOTION_CATEGORY_MAP = {
        'frustrated': 'frustration_support',
        'anxious': 'frustration_support',
        'sad': 'frustration_support',
        'happy': 'encouragement',
        'excited': 'encouragement',
        'bored': 'boredom_challenge',
        'confused': 'challenge_help',
        'proud': 'encouragement',
        'curious': 'socratic_question',
        'flow': 'flow_state',
        'engaged': 'encouragement',
        'neutral': 'general',
    }

    # Markov-style phrase variations for naturalness
    PHRASE_VARIATIONS = {
        'I think': ['I believe', 'In my view', 'My sense is', 'It seems to me'],
        'Great job': ['Well done', 'Excellent work', 'Impressive', 'Nicely done'],
        'Keep going': ['Keep it up', 'Stay the course', 'Press on', "Don't stop now"],
        'You can do it': ["You've got this", 'You can handle it', 'Believe in yourself', 'I know you can'],
        "That's right": ['Exactly', 'Spot on', 'Correct', 'Precisely'],
        "Let's try": ['How about we', 'Shall we', 'Want to', "Let's give it a shot and"],
        'I understand': ['I get it', 'I hear you', 'Makes sense', 'Totally fair'],
        "Don't worry": ['No worries', "It's all good", "Don't sweat it", 'Relax'],
        'Remember': ['Keep in mind', "Don't forget", 'Think about this:', "Here's the thing:"],
        'Try again': ['Give it another go', 'Take another shot', 'One more attempt', 'Have another crack at it'],
    }

    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #
    @classmethod
    def generate_response(
        cls,
        player,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a contextual response without any external API.

        Parameters
        ----------
        player : accounts.Player
            The player object (with relations: streak, assessment, etc.).
        message : str
            The player's text message.
        context : dict or None
            Optional context with keys like ``realm``, ``challenge_id``,
            ``session_data``, ``is_first_message``, ``conversation_history``,
            ``context_type``, ``challenge_score``, ``challenge_trait``,
            ``challenge_difficulty``, ``realm_name``, ``streak``, ``level``.

        Returns
        -------
        dict
            {
                'text': str,           # The response text
                'response': str,       # Alias for 'text' (backward compat)
                'emotion': str,        # Inferred emotion
                'emotion_confidence': float,
                'strategy': str,       # Coaching strategy used
                'coaching_strategy': str,  # Alias (backward compat)
                'intent': str,         # Classified intent
                'category': str,       # Template category used
                'suggestions': list,   # Follow-up action suggestions
            }
        """
        context = context or {}

        # 1. Classify intent
        intent = cls._classify_intent(message)

        # 2. Build player context
        player_ctx = cls._build_player_context(player, context)

        # 3. Infer emotion
        session_data = context.get('session_data')
        emotion, emotion_conf = EmotionEngine.combined(message, session_data)

        # 4. Select coaching strategy
        personality = player_ctx.get('personality')
        strategy = CoachingStrategy.select(
            emotion, emotion_conf, personality, session_data,
        )

        # 5. Select template category
        category = cls._select_category(intent, emotion, context)

        # 6. Get and filter templates
        templates = cls._get_templates(category, context)
        filtered = filter_by_personality(templates, personality)

        # Also add coaching templates for additional variety
        coaching_templates = CoachingStrategy.get_templates(
            strategy, cls._coaching_phase(context),
        )

        # 7. Select and fill template
        template_ctx = cls._build_template_context(player_ctx, context)
        text = cls._select_and_fill(
            filtered, coaching_templates, template_ctx, player, message,
        )

        # 8. Apply Markov variation
        text = cls._apply_variation(text, player)

        # 9. Handle special cases
        text = cls._handle_special_cases(text, intent, emotion, player_ctx, context)

        # 10. Generate suggestions
        suggestions = cls._generate_suggestions(player, emotion, context)

        return {
            'text': text,
            'response': text,  # backward compat
            'emotion': emotion,
            'emotion_confidence': emotion_conf,
            'strategy': strategy,
            'coaching_strategy': strategy,  # backward compat
            'intent': intent,
            'category': category,
            'suggestions': suggestions,
        }

    # ------------------------------------------------------------------ #
    # Backward-compatible class methods
    # ------------------------------------------------------------------ #
    @classmethod
    def detect_emotion(cls, message: str) -> str:
        """Detect emotion from message text (backward compat wrapper).

        Parameters
        ----------
        message : str
            The player's message text.

        Returns
        -------
        str
            Detected emotion label.
        """
        emotion, _ = EmotionEngine.from_text(message)
        return emotion

    @classmethod
    def select_coaching_strategy(cls, emotion: str, context: Optional[Dict] = None) -> str:
        """Select coaching strategy (backward compat wrapper).

        Parameters
        ----------
        emotion : str
            Detected player emotion.
        context : dict, optional
            Additional context.

        Returns
        -------
        str
            Coaching strategy name.
        """
        session_data = context or {}
        return CoachingStrategy.select(emotion, 0.5, None, session_data)

    # ------------------------------------------------------------------ #
    # Intent classification
    # ------------------------------------------------------------------ #
    @classmethod
    def _classify_intent(cls, message: str) -> str:
        """Classify message intent using keyword matching.

        Returns the intent with the most keyword hits, or 'general'.
        """
        if not message or not message.strip():
            return 'general'

        message_lower = message.lower().strip()
        scores: Dict[str, int] = {}

        for intent, keywords in cls.INTENT_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in message_lower)
            if count > 0:
                scores[intent] = count

        if not scores:
            return 'general'

        return max(scores, key=scores.get)

    # ------------------------------------------------------------------ #
    # Player context
    # ------------------------------------------------------------------ #
    @classmethod
    def _build_player_context(cls, player, context: Dict) -> Dict:
        """Build a comprehensive player context dict for template filling."""
        ctx: Dict[str, Any] = {
            'name': player.display_name,
            'level': player.overall_level,
            'xp': player.total_xp,
            'streak': 0,
            'personality': None,
            'companion_profile': None,
            'realm': context.get('realm') or context.get('realm_name', 'MindArena'),
            'realm_level': 1,
        }

        # Streak (from context or model)
        if 'streak' in context:
            ctx['streak'] = context['streak']
        else:
            try:
                ctx['streak'] = player.streak.current_streak
            except Exception:
                pass

        # Level override from context
        if 'level' in context:
            ctx['level'] = context['level']

        # Personality assessment (Big Five + EI)
        try:
            assessment = player.assessment
            ctx['personality'] = {
                'openness': assessment.openness,
                'conscientiousness': assessment.conscientiousness,
                'extraversion': assessment.extraversion,
                'agreeableness': assessment.agreeableness,
                'neuroticism': assessment.neuroticism,
                'self_awareness': assessment.self_awareness,
                'empathy': assessment.empathy,
                'emotional_regulation': assessment.emotional_regulation,
                'social_skills': assessment.social_skills,
                'analytical_thinking': assessment.analytical_thinking,
                'creative_thinking': assessment.creative_thinking,
                'practical_thinking': assessment.practical_thinking,
                'risk_tolerance': assessment.risk_tolerance,
            }
        except Exception:
            pass

        # Companion profile (warmth, directness, humor, etc.)
        try:
            profile = player.companion_profile
            ctx['companion_profile'] = {
                'warmth': profile.warmth,
                'directness': profile.directness,
                'humor': profile.humor,
                'formality': profile.formality,
                'challenge_level': profile.challenge_level,
            }
        except Exception:
            pass

        # Realm stats
        realm_slug = context.get('realm_slug') or context.get('realm', '')
        if realm_slug:
            try:
                from apps.progression.models import PlayerRealmStat
                stat = PlayerRealmStat.objects.filter(
                    player=player, realm__slug=realm_slug,
                ).first()
                if stat:
                    ctx['realm_level'] = stat.realm_level
                    ctx['realm'] = stat.realm.name_en
            except Exception:
                pass

        # Time of day
        ctx['time_of_day'] = cls._get_time_of_day()

        # Accuracy from session data
        session_data = context.get('session_data', {})
        if session_data:
            accuracy = session_data.get('accuracy', 0.5)
            ctx['accuracy'] = f"{accuracy * 100:.0f}"
        else:
            ctx['accuracy'] = '---'

        return ctx

    # ------------------------------------------------------------------ #
    # Category selection
    # ------------------------------------------------------------------ #
    @classmethod
    def _select_category(cls, intent: str, emotion: str, context: Dict) -> str:
        """Select the best template category based on intent and emotion."""
        # Check for special contexts first
        if context.get('is_first_message') or context.get('context_type') == 'greeting':
            return 'greeting'

        if context.get('is_level_up') or context.get('context_type') == 'level_up':
            return 'level_up'

        if context.get('is_streak_milestone') or context.get('context_type') == 'streak':
            return 'streak_milestone'

        # Post-challenge context
        context_type = context.get('context_type', '')
        if context_type == 'post_challenge':
            score = context.get('challenge_score', 0)
            if score >= 70:
                return 'encouragement'
            return 'frustration_support'

        if context_type == 'realm_exploration':
            return 'realm_specific'

        # Intent-based category
        category = cls.INTENT_CATEGORY_MAP.get(intent)

        # If intent maps to None, determine from emotion
        if category is None:
            category = cls.EMOTION_CATEGORY_MAP.get(emotion, 'general')

        # Realm-specific intent needs the realm sub-category
        if intent == 'realm':
            category = 'realm_specific'

        return category

    # ------------------------------------------------------------------ #
    # Template retrieval
    # ------------------------------------------------------------------ #
    @classmethod
    def _get_templates(cls, category: str, context: Dict) -> list:
        """Get templates for the selected category."""
        if category == 'realm_specific':
            realm_slug = (
                context.get('realm_slug')
                or context.get('realm')
                or context.get('realm_name', '')
            )
            return get_realm_templates(realm_slug)

        templates = TEMPLATES.get(category)
        if templates is None:
            return TEMPLATES.get('general', [])

        if isinstance(templates, list):
            return templates

        # Handle dict (e.g., realm_specific used as flat fallback)
        if isinstance(templates, dict):
            all_templates: List = []
            for sub_list in templates.values():
                if isinstance(sub_list, list):
                    all_templates.extend(sub_list)
            return all_templates

        return TEMPLATES.get('general', [])

    # ------------------------------------------------------------------ #
    # Coaching phase
    # ------------------------------------------------------------------ #
    @classmethod
    def _coaching_phase(cls, context: Dict) -> str:
        """Determine which coaching phase we're in based on conversation."""
        history = context.get('conversation_history', [])
        if not history:
            return 'opening'
        if len(history) >= 6:
            return 'closing'
        return 'follow_up'

    # ------------------------------------------------------------------ #
    # Template selection and filling
    # ------------------------------------------------------------------ #
    @classmethod
    def _select_and_fill(
        cls,
        category_templates: List[str],
        coaching_templates: List[str],
        template_ctx: Dict,
        player,
        message: str,
    ) -> str:
        """Select the best template and fill its placeholders."""
        # Combine category templates with coaching templates
        all_templates = list(category_templates)
        all_templates.extend(coaching_templates)

        if not all_templates:
            name = template_ctx.get('name', 'Player')
            return f"I'm here for you, {name}. What can I help with?"

        # Deterministic-ish selection for variety:
        # Hash of message + player name + hour ensures different inputs get
        # different templates, but the same input within the same hour is
        # consistent (avoids duplicate responses in rapid succession).
        seed_str = f"{message}_{player.display_name}_{datetime.now().strftime('%Y%m%d%H')}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        selected = rng.choice(all_templates)

        return fill_template(selected, template_ctx)

    # ------------------------------------------------------------------ #
    # Template context
    # ------------------------------------------------------------------ #
    @classmethod
    def _build_template_context(cls, player_ctx: Dict, context: Dict) -> Dict:
        """Build the placeholder context dict for template filling."""
        ctx = {
            'name': player_ctx.get('name', 'Player'),
            'level': player_ctx.get('level', 1),
            'streak': player_ctx.get('streak', 0),
            'xp': player_ctx.get('xp', 0),
            'realm': player_ctx.get('realm', 'MindArena'),
            'realm_level': player_ctx.get('realm_level', 1),
            'accuracy': player_ctx.get('accuracy', '---'),
            'time_of_day': player_ctx.get('time_of_day', 'day'),
        }

        # Add any context-provided formatting values
        for key in ('trait', 'difficulty', 'score', 'challenge_trait',
                     'challenge_difficulty', 'challenge_score',
                     'realm_name', 'realm_trait'):
            if key in context:
                ctx[key] = context[key]

        return ctx

    # ------------------------------------------------------------------ #
    # Markov-style phrase variation
    # ------------------------------------------------------------------ #
    @classmethod
    def _apply_variation(cls, text: str, player) -> str:
        """Apply light phrase variations for naturalness.

        Uses player name + date as seed so the same player gets consistent
        but daily-varied phrasing.
        """
        seed_str = f"{player.display_name}_{datetime.now().strftime('%Y%m%d')}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        result = text
        for phrase, alternatives in cls.PHRASE_VARIATIONS.items():
            if phrase in result:
                # 40% chance to substitute for variety
                if rng.random() < 0.4:
                    replacement = rng.choice(alternatives)
                    result = result.replace(phrase, replacement, 1)

        return result

    # ------------------------------------------------------------------ #
    # Special case handling
    # ------------------------------------------------------------------ #
    @classmethod
    def _handle_special_cases(
        cls, text: str, intent: str, emotion: str,
        player_ctx: Dict, context: Dict,
    ) -> str:
        """Add special prefixes/suffixes for certain situations."""
        additions: List[str] = []

        # First message of the day: add streak milestone
        if context.get('is_first_message') and player_ctx.get('streak', 0) > 0:
            streak = player_ctx['streak']
            name = player_ctx['name']
            milestones = (7, 14, 21, 30, 50, 75, 100, 150, 200, 365)
            if streak in milestones:
                additions.append(
                    f"Wow, {name}! {streak}-day streak milestone! That's incredible dedication. "
                )

        # Emotional distress: add supportive prefix
        if emotion in ('sad', 'anxious') and EmotionEngine.needs_support(emotion):
            has_acknowledgment = any(
                word in text.lower()
                for word in ['okay', 'ok', 'alright', 'hear you', 'understand', 'valid']
            )
            if not has_acknowledgment:
                additions.insert(0, "I hear you, and what you're feeling is valid. ")

        # Level up context
        if context.get('is_level_up') or context.get('context_type') == 'level_up':
            new_level = player_ctx.get('level', 1)
            if new_level % 10 == 0:
                additions.append(f" Level {new_level} is a MAJOR milestone!")
            elif new_level % 5 == 0:
                additions.append(f" Level {new_level} -- that's a great milestone!")

        if additions:
            prefix = ''.join(additions[:1])
            suffix = ''.join(additions[1:])
            text = prefix + text + suffix

        return text.strip()

    # ------------------------------------------------------------------ #
    # Suggestion generation
    # ------------------------------------------------------------------ #
    @classmethod
    def _generate_suggestions(
        cls,
        player,
        emotion: str,
        context: Optional[Dict] = None,
    ) -> List[str]:
        """Generate follow-up action suggestions based on emotion/context.

        Returns
        -------
        list[str]
            Up to 3 suggested actions for the player.
        """
        if emotion == 'frustrated':
            return [
                "Try an easier challenge to build confidence",
                "Review a topic you've already mastered",
                "Take a short break and come back refreshed",
            ]
        if emotion in ('sad', 'anxious'):
            return [
                "Start with something familiar and comfortable",
                "Try a relaxed, untimed challenge",
                "Explore the Wellness Grove for a calming session",
            ]
        if emotion == 'bored':
            return [
                "Explore a new realm you haven't tried",
                "Try a harder difficulty level",
                "Challenge a friend in the arena",
            ]
        if emotion in ('happy', 'proud', 'excited'):
            return [
                "Keep the momentum with another challenge",
                "Try a harder version of what you just completed",
                "Share your achievement with friends",
            ]
        if emotion == 'curious':
            return [
                "Explore the learning path for this topic",
                "Try a related challenge in a different realm",
                "Check your knowledge radar for growth areas",
            ]
        if emotion == 'confused':
            return [
                "Re-read the challenge description carefully",
                "Try breaking the problem into smaller parts",
                "Ask Noor for a hint on this specific challenge",
            ]
        if emotion == 'flow':
            return [
                "Keep going -- you're in the zone!",
                "Try the next difficulty level while you're sharp",
                "Set a personal best goal for this session",
            ]

        # Default / neutral / engaged
        return [
            "Check your recommended challenges",
            "Continue your learning path",
            "Review your progress dashboard",
        ]

    # ------------------------------------------------------------------ #
    # Quick response (minimal context needed)
    # ------------------------------------------------------------------ #
    @classmethod
    def quick_response(cls, player_name: str, message: str, emotion_hint: Optional[str] = None) -> str:
        """Generate a quick response with minimal player context.

        Useful for testing or when full player data isn't available.

        Parameters
        ----------
        player_name : str
            Player's display name.
        message : str
            Player's message.
        emotion_hint : str or None
            Override emotion detection.

        Returns
        -------
        str
            The response text.
        """
        # Classify intent
        intent = cls._classify_intent(message)

        # Detect emotion
        if emotion_hint:
            emotion = emotion_hint
        else:
            emotion, _ = EmotionEngine.from_text(message)

        # Select category
        category = cls.INTENT_CATEGORY_MAP.get(intent)
        if category is None:
            category = cls.EMOTION_CATEGORY_MAP.get(emotion, 'general')

        # Get templates
        templates = TEMPLATES.get(category)
        if isinstance(templates, dict):
            all_t: List = []
            for sub in templates.values():
                if isinstance(sub, list):
                    all_t.extend(sub)
            templates = all_t
        if not templates:
            templates = TEMPLATES.get('general', [])

        # Filter to plain strings only
        plain = [t if isinstance(t, str) else t.get('text', '') for t in templates]

        if not plain:
            return f"I'm here for you, {player_name}!"

        # Pick a template deterministically
        seed_str = f"{message}_{player_name}_{datetime.now().strftime('%Y%m%d%H')}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        selected = rng.choice(plain)

        # Fill context
        ctx = {
            'name': player_name,
            'level': '?',
            'streak': '?',
            'xp': '?',
            'realm': 'MindArena',
            'realm_level': '?',
            'accuracy': '---',
            'time_of_day': cls._get_time_of_day(),
        }
        return fill_template(selected, ctx)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _get_time_of_day() -> str:
        """Return current time of day as a string."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return 'morning'
        if 12 <= hour < 17:
            return 'afternoon'
        if 17 <= hour < 21:
            return 'evening'
        return 'night'

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Return engine statistics for debugging/admin dashboards."""
        from .templates import get_category_counts, get_template_count
        return {
            'total_templates': get_template_count(),
            'categories': get_category_counts(),
            'intents': list(cls.INTENT_KEYWORDS.keys()),
            'emotions': list(EmotionEngine.EMOTION_KEYWORDS.keys()),
            'strategies': CoachingStrategy.get_all_strategy_names(),
            'phrase_variations': len(cls.PHRASE_VARIATIONS),
        }
