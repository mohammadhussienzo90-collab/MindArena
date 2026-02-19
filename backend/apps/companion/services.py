"""AI Companion service using Claude API."""
from django.conf import settings
from pathlib import Path


class CompanionService:
    SYSTEM_PROMPT_PATH = Path(__file__).parent / 'system_prompt.txt'

    @classmethod
    def get_system_prompt(cls, player):
        """Build system prompt with player context."""
        if cls.SYSTEM_PROMPT_PATH.exists():
            base_prompt = cls.SYSTEM_PROMPT_PATH.read_text()
        else:
            base_prompt = (
                "You are Noor, an AI companion in MindArena. "
                "You guide the player through self-development challenges. "
                "Be encouraging, insightful, and adapt to the player's personality."
            )

        player_context = f"""
Player: {player.display_name}
Level: {player.overall_level}
Language: {player.preferred_lang}
"""
        try:
            assessment = player.assessment
            player_context += f"""
Personality Traits:
- Openness: {assessment.openness}/100
- Conscientiousness: {assessment.conscientiousness}/100
- Extraversion: {assessment.extraversion}/100
- Empathy: {assessment.empathy}/100
- Analytical: {assessment.analytical_thinking}/100
- Creative: {assessment.creative_thinking}/100
"""
        except Exception:
            player_context += "\nPersonality: Not yet assessed\n"

        return f"{base_prompt}\n\n--- PLAYER CONTEXT ---\n{player_context}"

    @classmethod
    def chat(cls, player, message, conversation=None):
        """Send a message and get companion response."""
        from .models import CompanionConversation, CompanionMessage

        if conversation is None:
            conversation = CompanionConversation.objects.create(
                player=player, context_type='general',
            )

        CompanionMessage.objects.create(
            conversation=conversation, role='player', content=message,
        )

        # Build message history
        history = CompanionMessage.objects.filter(
            conversation=conversation,
        ).order_by('created_at')[:20]

        messages = []
        for msg in history:
            role = 'user' if msg.role == 'player' else 'assistant'
            messages.append({'role': role, 'content': msg.content})

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=getattr(settings, 'COMPANION_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=500,
                system=cls.get_system_prompt(player),
                messages=messages,
            )
            reply = response.content[0].text
        except Exception as e:
            reply = f"I'm having trouble connecting right now. Let's try again in a moment. ({type(e).__name__})"

        CompanionMessage.objects.create(
            conversation=conversation, role='companion', content=reply,
        )

        return {
            'conversation_id': conversation.id,
            'reply': reply,
        }
