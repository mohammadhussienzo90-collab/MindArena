"""AI Companion service using Claude API."""
from django.conf import settings

from .prompts import build_system_prompt


class CompanionService:

    @classmethod
    def get_system_prompt(cls, player, context_type='general', realm_slug=None):
        """Build system prompt with full player context and personality adaptation."""
        return build_system_prompt(
            player,
            context_type=context_type,
            realm_slug=realm_slug,
        )

    @classmethod
    def chat(cls, player, message, conversation=None, context_type=None,
             realm_slug=None):
        """Send a message and get companion response."""
        from .models import CompanionConversation, CompanionMessage

        if conversation is None:
            conversation = CompanionConversation.objects.create(
                player=player, context_type=context_type or 'general',
            )

        # Derive context_type from the conversation if not explicitly passed
        effective_context = context_type or conversation.context_type or 'general'

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
                model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=500,
                system=cls.get_system_prompt(
                    player,
                    context_type=effective_context,
                    realm_slug=realm_slug,
                ),
                messages=messages,
            )
            reply = response.content[0].text
        except Exception:
            # Fallback to Smart Noor (no external API needed)
            try:
                from apps.ai_engine.noor.engine import SmartNoorEngine
                noor_result = SmartNoorEngine.generate_response(
                    player=player, message=message,
                    context={'context_type': effective_context, 'realm_slug': realm_slug},
                )
                reply = noor_result if isinstance(noor_result, str) else noor_result.get('response', noor_result.get('text', ''))
            except Exception:
                reply = (
                    "I'm here for you! Let's keep going. "
                    "What would you like to explore next?"
                )

        CompanionMessage.objects.create(
            conversation=conversation, role='companion', content=reply,
        )

        return {
            'conversation_id': conversation.id,
            'reply': reply,
        }
