from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.core.throttles import CompanionRateThrottle
from .models import CompanionConversation
from .serializers import CompanionChatSerializer, CompanionMessageSerializer
from .services import CompanionService


class CompanionChatView(views.APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CompanionRateThrottle]

    def post(self, request):
        serializer = CompanionChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conversation = None
        conv_id = serializer.validated_data.get('conversation_id')
        if conv_id:
            try:
                conversation = CompanionConversation.objects.get(
                    id=conv_id, player=request.user.player,
                )
            except CompanionConversation.DoesNotExist:
                pass

        result = CompanionService.chat(
            player=request.user.player,
            message=serializer.validated_data['message'],
            conversation=conversation,
            context_type=serializer.validated_data.get('context_type', 'general'),
            realm_slug=serializer.validated_data.get('realm_slug'),
        )

        # Check for companion-related achievements
        from apps.progression.achievement_checker import AchievementChecker
        new_achievements = AchievementChecker.check_specific(
            request.user.player, 'companion_chat',
        )
        if new_achievements:
            result['new_achievements'] = new_achievements

        return Response(result)


class CompanionConversationListView(views.APIView):
    """List all conversations for the authenticated player."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = CompanionConversation.objects.filter(
            player=request.user.player,
        ).order_by('-started_at')[:20]

        data = []
        for conv in conversations:
            last_msg = conv.messages.order_by('-created_at').first()
            data.append({
                'id': conv.id,
                'context_type': conv.context_type,
                'started_at': conv.started_at.isoformat(),
                'message_count': conv.messages.count(),
                'last_message': last_msg.content[:100] if last_msg else '',
                'last_message_at': last_msg.created_at.isoformat() if last_msg else None,
            })
        return Response({'conversations': data})


class CompanionHistoryView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conv = CompanionConversation.objects.get(
                id=conversation_id, player=request.user.player,
            )
        except CompanionConversation.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        messages = conv.messages.all()
        return Response(CompanionMessageSerializer(messages, many=True).data)
