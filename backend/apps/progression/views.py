from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    PlayerRealmStat, PlayerChallengeResult, PlayerQuestProgress,
    Achievement, PlayerAchievement, DailyStreak,
)
from .serializers import (
    PlayerRealmStatSerializer, PlayerChallengeResultSerializer,
    PlayerQuestProgressSerializer, AchievementSerializer,
    PlayerAchievementSerializer, DailyStreakSerializer,
)


class ProgressionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        player = request.user.player
        realm_stats = PlayerRealmStat.objects.filter(player=player).select_related('realm')
        streak = DailyStreak.objects.filter(player=player).first()
        return Response({
            'overall_level': player.overall_level,
            'total_xp': player.total_xp,
            'realm_stats': PlayerRealmStatSerializer(realm_stats, many=True).data,
            'streak': DailyStreakSerializer(streak).data if streak else None,
        })

    @action(detail=False, methods=['get'])
    def history(self, request):
        player = request.user.player
        results = PlayerChallengeResult.objects.filter(
            player=player
        ).select_related('challenge')[:50]
        return Response(PlayerChallengeResultSerializer(results, many=True).data)

    @action(detail=False, methods=['get'])
    def quests(self, request):
        player = request.user.player
        progress = PlayerQuestProgress.objects.filter(
            player=player
        ).select_related('quest')
        return Response(PlayerQuestProgressSerializer(progress, many=True).data)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.filter(is_hidden=False)
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def earned(self, request):
        earned = PlayerAchievement.objects.filter(
            player=request.user.player
        ).select_related('achievement')
        return Response(PlayerAchievementSerializer(earned, many=True).data)
