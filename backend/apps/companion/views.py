from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CompanionConversation
from .serializers import CompanionChatSerializer, CompanionMessageSerializer
from .services import CompanionService


class CompanionChatView(views.APIView):
    permission_classes = [IsAuthenticated]

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
