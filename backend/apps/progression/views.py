import hashlib
from datetime import date

from rest_framework import viewsets, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import Player
from apps.realms.models import Challenge, Realm
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

    def history(self, request):
        from rest_framework.pagination import PageNumberPagination
        player = request.user.player
        results = PlayerChallengeResult.objects.filter(
            player=player
        ).select_related('challenge').order_by('-played_at')

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(results, request)
        if page is not None:
            return paginator.get_paginated_response(
                PlayerChallengeResultSerializer(page, many=True).data
            )
        return Response(PlayerChallengeResultSerializer(results[:50], many=True).data)

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


class LeaderboardView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 100)
        realm_slug = request.query_params.get('realm')

        if realm_slug:
            # Realm-specific leaderboard
            stats = PlayerRealmStat.objects.filter(
                realm__slug=realm_slug,
            ).select_related('player', 'realm').order_by('-realm_xp')[:limit]
            entries = [
                {
                    'rank': i + 1,
                    'display_name': s.player.display_name,
                    'realm_level': s.realm_level,
                    'realm_xp': s.realm_xp,
                    'challenges_completed': s.challenges_completed,
                }
                for i, s in enumerate(stats)
            ]
        else:
            # Global leaderboard
            players = Player.objects.order_by('-total_xp')[:limit]
            entries = [
                {
                    'rank': i + 1,
                    'display_name': p.display_name,
                    'overall_level': p.overall_level,
                    'total_xp': p.total_xp,
                }
                for i, p in enumerate(players)
            ]

        # Include requesting player's rank
        player = request.user.player
        if realm_slug:
            stat = PlayerRealmStat.objects.filter(
                player=player, realm__slug=realm_slug,
            ).first()
            my_rank = PlayerRealmStat.objects.filter(
                realm__slug=realm_slug, realm_xp__gt=(stat.realm_xp if stat else 0),
            ).count() + 1
        else:
            my_rank = Player.objects.filter(total_xp__gt=player.total_xp).count() + 1

        return Response({
            'leaderboard': entries,
            'my_rank': my_rank,
            'my_display_name': player.display_name,
        })


class DailyChallengeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return one daily challenge per realm, deterministic by date."""
        today = date.today()
        realms = Realm.objects.all()
        daily_challenges = []

        for realm in realms:
            challenges = list(
                Challenge.objects.filter(
                    quest__realm=realm, is_active=True,
                ).values_list('id', flat=True)
            )
            if not challenges:
                continue
            # Deterministic pick: hash(date + realm_slug) mod count
            seed = hashlib.md5(
                f"{today.isoformat()}-{realm.slug}".encode()
            ).hexdigest()
            index = int(seed, 16) % len(challenges)
            challenge_id = challenges[index]
            daily_challenges.append({
                'realm_slug': realm.slug,
                'realm_name_en': realm.name_en,
                'realm_name_ar': getattr(realm, 'name_ar', ''),
                'challenge_id': challenge_id,
                'color': realm.color_primary,
            })

        # Check which ones the player already completed today
        from django.utils import timezone
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        completed_ids = set(
            PlayerChallengeResult.objects.filter(
                player=request.user.player,
                played_at__gte=today_start,
            ).values_list('challenge_id', flat=True)
        )

        for dc in daily_challenges:
            dc['completed_today'] = dc['challenge_id'] in completed_ids

        return Response({
            'date': today.isoformat(),
            'challenges': daily_challenges,
        })
