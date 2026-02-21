"""AI Companion service — hybrid Claude API + offline SmartNoorEngine."""
import logging

from django.conf import settings

from .prompts import build_system_prompt

logger = logging.getLogger(__name__)


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
        """Send a message and get companion response.

        Strategy:
        1. Try Claude API (online, deep understanding) — uses noor_prompts.py as system prompt
        2. Fall back to SmartNoorEngine (offline, template-based, zero API calls)
        3. Final fallback: generic supportive response
        """
        from .models import CompanionConversation, CompanionMessage

        if conversation is None:
            conversation = CompanionConversation.objects.create(
                player=player, context_type=context_type or 'general',
            )

        effective_context = context_type or conversation.context_type or 'general'

        CompanionMessage.objects.create(
            conversation=conversation, role='player', content=message,
        )

        # Build message history for Claude
        history = CompanionMessage.objects.filter(
            conversation=conversation,
        ).order_by('created_at')[:20]

        messages = []
        for msg in history:
            role = 'user' if msg.role == 'player' else 'assistant'
            messages.append({'role': role, 'content': msg.content})

        # Always run offline emotion detection for metadata
        emotion_data = cls._detect_emotion(player, message, effective_context, realm_slug)

        reply = None
        source = 'fallback'

        # Strategy 1: Claude API (online)
        if getattr(settings, 'ANTHROPIC_API_KEY', ''):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = client.messages.create(
                    model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
                    max_tokens=getattr(settings, 'COMPANION_MAX_TOKENS', 300),
                    system=cls.get_system_prompt(
                        player,
                        context_type=effective_context,
                        realm_slug=realm_slug,
                    ),
                    messages=messages,
                )
                reply = response.content[0].text
                source = 'claude'
            except Exception as e:
                logger.warning("Claude API failed, falling back to SmartNoor: %s", e)

        # Strategy 2: SmartNoorEngine (offline)
        if reply is None:
            try:
                from apps.ai_engine.noor.engine import SmartNoorEngine
                noor_result = SmartNoorEngine.generate_response(
                    player=player, message=message,
                    context={
                        'context_type': effective_context,
                        'realm_slug': realm_slug,
                    },
                )
                if isinstance(noor_result, str):
                    reply = noor_result
                else:
                    reply = noor_result.get('response', noor_result.get('text', ''))
                    # Merge richer data from noor
                    emotion_data.update({
                        k: v for k, v in noor_result.items()
                        if k in ('emotion', 'emotion_confidence', 'strategy',
                                 'coaching_strategy', 'intent', 'category',
                                 'suggestions')
                    })
                source = 'noor'
            except Exception as e:
                logger.warning("SmartNoorEngine failed: %s", e)

        # Strategy 3: Generic fallback
        if reply is None:
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
            'source': source,
            'emotion': emotion_data.get('emotion', 'neutral'),
            'emotion_confidence': emotion_data.get('emotion_confidence', 0.5),
            'coaching_strategy': emotion_data.get('strategy', emotion_data.get('coaching_strategy', '')),
            'suggestions': emotion_data.get('suggestions', []),
        }

    @classmethod
    def _detect_emotion(cls, player, message, context_type, realm_slug):
        """Run offline emotion detection regardless of which response strategy is used."""
        try:
            from apps.ai_engine.noor.emotion import EmotionEngine
            emotion, confidence = EmotionEngine.combined(message)
            return {
                'emotion': emotion,
                'emotion_confidence': confidence,
            }
        except Exception:
            return {
                'emotion': 'neutral',
                'emotion_confidence': 0.5,
            }
