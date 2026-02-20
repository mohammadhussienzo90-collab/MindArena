from django.contrib.auth import update_session_auth_hash
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.throttles import AuthRateThrottle
from .serializers import RegisterSerializer, PlayerSerializer, PlayerUpdateSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'player': PlayerSerializer(user.player).data,
        }, status=status.HTTP_201_CREATED)


class PlayerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        return Response(PlayerSerializer(player).data)

    def patch(self, request):
        player = request.user.player
        serializer = PlayerUpdateSerializer(player, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PlayerSerializer(player).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')

        if not old_password or not new_password:
            return Response(
                {'detail': 'Both old_password and new_password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {'detail': 'New password must be at least 8 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not user.check_password(old_password):
            return Response(
                {'detail': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        # Issue new tokens since password changed
        refresh = RefreshToken.for_user(user)
        return Response({
            'detail': 'Password changed successfully.',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
        })


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password', '')
        if not request.user.check_password(password):
            return Response(
                {'detail': 'Password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete the user (cascades to Player and all related data)
        request.user.delete()
        return Response(
            {'detail': 'Account deleted.'},
            status=status.HTTP_200_OK,
        )


class PlayerSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response(
                {'detail': 'Search query must be at least 2 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .models import Player
        players = Player.objects.filter(
            display_name__icontains=query,
        ).exclude(
            user=request.user,
        ).values(
            'id', 'display_name', 'overall_level', 'total_xp',
            'avatar_preset',
        )[:20]

        return Response({'results': list(players)})


class PublicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id):
        from .models import Player
        from apps.progression.models import PlayerRealmStat, PlayerAchievement

        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            return Response(
                {'detail': 'Player not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        realm_stats = PlayerRealmStat.objects.filter(
            player=player,
        ).select_related('realm').values(
            'realm__slug', 'realm__name_en', 'realm_level', 'realm_xp',
            'challenges_completed',
        )

        achievements_count = PlayerAchievement.objects.filter(
            player=player,
        ).count()

        return Response({
            'id': player.id,
            'display_name': player.display_name,
            'overall_level': player.overall_level,
            'total_xp': player.total_xp,
            'avatar_preset': player.avatar_preset,
            'realm_stats': list(realm_stats),
            'achievements_count': achievements_count,
            'member_since': player.created_at.date().isoformat(),
        })
