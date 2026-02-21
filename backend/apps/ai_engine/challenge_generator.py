"""
AI-Powered Challenge Generator
================================
Uses Claude API to generate personalized challenges targeting player knowledge gaps.
Falls back gracefully when API is unavailable.

Usage:
    from apps.ai_engine.challenge_generator import ChallengeGenerator
    challenges = ChallengeGenerator.generate_for_player(player, 'logic_fortress', count=3)
"""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Challenge type definitions for the AI prompt
CHALLENGE_TYPE_SPECS = {
    "multiple_choice": {
        "description": "4 options, one correct answer",
        "fields": "question_en, question_ar, options_en (4 strings), options_ar (4 strings), correct_index (0-3), explanation_en, explanation_ar",
    },
    "scenario_choice": {
        "description": "Situational scenario with 4 contextual choices",
        "fields": "question_en, question_ar, options_en (4 strings), options_ar (4 strings), correct_index (0-3), explanation_en, explanation_ar",
    },
    "math_logic": {
        "description": "Mathematical or logical puzzle with 4 possible answers",
        "fields": "question_en, question_ar, options_en (4 strings), options_ar (4 strings), correct_index (0-3), explanation_en, explanation_ar",
    },
}

REALM_THEMES = {
    "logic_fortress": "logical reasoning, pattern recognition, mathematical thinking, spatial puzzles",
    "emotion_ocean": "emotional intelligence, empathy, self-awareness, conflict resolution, body language",
    "creativity_nebula": "lateral thinking, creative problem-solving, reframing, divergent thinking",
    "discipline_citadel": "habit building, time management, willpower, goal setting, self-control",
    "knowledge_peaks": "cognitive science, memory techniques, learning strategies, psychology, biases",
    "social_bridge": "communication, negotiation, active listening, leadership, teamwork",
    "wealth_garden": "financial literacy, investing, budgeting, compound interest, value creation",
    "wellness_grove": "stress management, sleep science, mindfulness, nutrition, physical health",
}


class ChallengeGenerator:
    """Generate personalized challenges using Claude API."""

    @classmethod
    def generate_for_player(cls, player, realm_slug, count=3):
        """Generate challenges targeting the player's knowledge gaps.

        Parameters
        ----------
        player : Player
            The player to generate challenges for.
        realm_slug : str
            Which realm the challenges should belong to.
        count : int
            Number of challenges to generate (1-5).

        Returns
        -------
        list[dict] | None
            List of challenge dicts ready for model creation, or None on failure.
        """
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
        if not api_key:
            logger.info("No ANTHROPIC_API_KEY — skipping challenge generation")
            return None

        count = max(1, min(5, count))
        gaps = cls._identify_gaps(player, realm_slug)
        prompt = cls._build_prompt(player, realm_slug, gaps, count)

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=2000,
                system=cls._system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            challenges = cls._parse_response(raw, realm_slug)
            logger.info(
                "Generated %d challenges for player %s in %s",
                len(challenges), player.id, realm_slug,
            )
            return challenges

        except Exception as e:
            logger.warning("Challenge generation failed: %s", e)
            return None

    @classmethod
    def _identify_gaps(cls, player, realm_slug):
        """Find the player's weakest skills in this realm using BKT."""
        gaps = []
        try:
            from apps.ai_engine.models import KnowledgeState
            states = KnowledgeState.objects.filter(
                player=player,
            ).order_by('p_known')[:5]
            for s in states:
                gaps.append({
                    'skill': s.skill,
                    'mastery': round(s.p_known, 2),
                })
        except Exception:
            pass

        if not gaps:
            gaps = [{'skill': 'general', 'mastery': 0.5}]
        return gaps

    @classmethod
    def _system_prompt(cls):
        return (
            "You are a challenge designer for MindArena, an educational game "
            "that develops real-life skills through gamified challenges. "
            "Generate challenges that are educational, engaging, and accurately "
            "test the specified skills. All challenges must be bilingual "
            "(English and Arabic). Return valid JSON only."
        )

    @classmethod
    def _build_prompt(cls, player, realm_slug, gaps, count):
        theme = REALM_THEMES.get(realm_slug, "general knowledge")
        gap_desc = ", ".join(
            f"{g['skill']} (mastery: {g['mastery']})" for g in gaps
        )

        # Determine appropriate difficulty
        try:
            from apps.progression.models import PlayerRealmStat
            stat = PlayerRealmStat.objects.filter(
                player=player, realm__slug=realm_slug,
            ).first()
            level = stat.realm_level if stat else 1
        except Exception:
            level = 1

        difficulty = min(level + 1, 8)

        return f"""Generate {count} challenges for the "{realm_slug}" realm.

Theme: {theme}
Target difficulty: {difficulty}/10
Player weaknesses: {gap_desc}
Player level: {level}

Each challenge must be a JSON object with these fields:
- "challenge_type": one of {list(CHALLENGE_TYPE_SPECS.keys())}
- "title_en": short English title
- "title_ar": short Arabic title
- "difficulty": integer 1-10
- "base_xp": integer 15-40 (higher for harder)
- "bonus_xp": integer 5-15
- "time_limit_secs": integer 30-90
- "content": object with: question_en, question_ar, options_en (array of 4), options_ar (array of 4), correct_index (0-3), explanation_en, explanation_ar

Return a JSON array of {count} challenge objects. No markdown, no explanation, just the JSON array."""

    @classmethod
    def _parse_response(cls, raw_text, realm_slug):
        """Parse Claude's response into validated challenge dicts."""
        # Strip markdown code fences if present
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.error("Failed to parse challenge JSON: %s", text[:200])
            return []

        if not isinstance(data, list):
            data = [data]

        valid = []
        for item in data:
            if cls._validate_challenge(item):
                item['realm_slug'] = realm_slug
                item['is_ai_generated'] = True
                valid.append(item)

        return valid

    @classmethod
    def _validate_challenge(cls, item):
        """Basic validation of a generated challenge."""
        required = ['challenge_type', 'title_en', 'difficulty', 'content']
        for field in required:
            if field not in item:
                return False

        content = item.get('content', {})
        if not isinstance(content, dict):
            return False

        # Must have question and options
        if 'question_en' not in content:
            return False
        if 'options_en' not in content or len(content.get('options_en', [])) != 4:
            return False
        if 'correct_index' not in content:
            return False

        return True
