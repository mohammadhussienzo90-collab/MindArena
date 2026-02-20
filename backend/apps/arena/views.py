"""Arena views — competitive matchmaking system."""
import logging

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.arena.models import ArenaMatch, PlayerArenaStats
from apps.arena.serializers import (
    ArenaMatchListSerializer,
    ArenaMatchDetailSerializer,
    ArenaMatchCreateSerializer,
    ArenaStatsSerializer,
    ArenaSubmitAnswerSerializer,
)
from apps.arena.services import ArenaService

logger = logging.getLogger(__name__)


class ArenaStatusView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'status': 'active',
            'message': 'The Arena is open! Challenge other players in head-to-head battles.',
            'match_types': [
                {'slug': 'speed', 'name': 'Speed Duel', 'players': 2},
                {'slug': 'strategic', 'name': 'Strategic Battle', 'players': 2},
                {'slug': 'team', 'name': 'Team Arena', 'players': 4},
            ],
        })


class ArenaMatchListView(views.APIView):
    """List open matches or player's match history."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filter_type = request.query_params.get('status', 'waiting')
        player = request.user.player

        if filter_type == 'mine':
            matches = ArenaMatch.objects.filter(
                participants__player=player,
            ).select_related('realm').distinct().order_by('-created_at')[:20]
        elif filter_type == 'waiting':
            matches = ArenaMatch.objects.filter(
                status='waiting', is_active=True,
            ).select_related('realm').order_by('-created_at')[:20]
        else:
            matches = ArenaMatch.objects.filter(
                status=filter_type, is_active=True,
            ).select_related('realm').order_by('-created_at')[:20]

        serializer = ArenaMatchListSerializer(matches, many=True)
        return Response(serializer.data)


class ArenaMatchDetailView(views.APIView):
    """Get details of a specific match."""
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):
        try:
            match = ArenaMatch.objects.select_related(
                'realm', 'winner',
            ).prefetch_related(
                'participants__player',
            ).get(id=match_id)
        except ArenaMatch.DoesNotExist:
            return Response(
                {'error': 'Match not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ArenaMatchDetailSerializer(match)
        return Response(serializer.data)


class ArenaCreateMatchView(views.APIView):
    """Create a new arena match."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ArenaMatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            match = ArenaService.create_match(
                player=request.user.player,
                match_type=serializer.validated_data['match_type'],
                realm_slug=serializer.validated_data['realm_slug'],
                total_rounds=serializer.validated_data['total_rounds'],
            )
        except Exception as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detail = ArenaMatchDetailSerializer(match)
        return Response(detail.data, status=status.HTTP_201_CREATED)


class ArenaJoinMatchView(views.APIView):
    """Join an existing waiting match."""
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):
        try:
            match = ArenaService.join_match(
                player=request.user.player,
                match_id=match_id,
            )
        except ArenaMatch.DoesNotExist:
            return Response(
                {'error': 'Match not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detail = ArenaMatchDetailSerializer(match)
        return Response(detail.data)


class ArenaFindMatchView(views.APIView):
    """Find an open match to join (matchmaking)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        match_type = request.query_params.get('match_type')
        realm_slug = request.query_params.get('realm_slug')

        match = ArenaService.find_match(
            player=request.user.player,
            match_type=match_type,
            realm_slug=realm_slug,
        )

        if match is None:
            return Response(
                {'match': None, 'message': 'No open matches found. Create one!'},
            )

        detail = ArenaMatchDetailSerializer(match)
        return Response({'match': detail.data})


class ArenaSubmitAnswerView(views.APIView):
    """Submit an answer for the current round."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ArenaSubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = ArenaService.submit_answer(
                player=request.user.player,
                match_id=serializer.validated_data['match_id'],
                round_number=serializer.validated_data['round_number'],
                challenge_id=serializer.validated_data['challenge_id'],
                answer=serializer.validated_data['answer'],
                time_taken_secs=serializer.validated_data['time_taken_secs'],
            )
        except ValueError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Also return the updated match state
        match = ArenaMatch.objects.get(id=serializer.validated_data['match_id'])
        match_data = ArenaMatchDetailSerializer(match).data

        return Response({
            'result': result,
            'match': match_data,
        })


class ArenaCurrentChallengeView(views.APIView):
    """Get the current challenge for an active match."""
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):
        try:
            match = ArenaMatch.objects.get(id=match_id, status='in_progress')
        except ArenaMatch.DoesNotExist:
            return Response(
                {'error': 'Active match not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify the player is a participant
        if not match.participants.filter(player=request.user.player).exists():
            return Response(
                {'error': 'You are not a participant in this match.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            challenge = ArenaService.get_current_challenge(match)
        except ValueError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'round_number': match.current_round,
            'total_rounds': match.total_rounds,
            'challenge': {
                'id': challenge.id,
                'slug': challenge.slug,
                'challenge_type': challenge.challenge_type,
                'title_en': challenge.title_en,
                'title_ar': challenge.title_ar,
                'content': challenge.content,
                'time_limit_secs': challenge.time_limit_secs or 30,
                'difficulty': challenge.difficulty,
            },
        })


class ArenaStatsView(views.APIView):
    """Get player's arena statistics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats, _ = PlayerArenaStats.objects.get_or_create(
            player=request.user.player,
            defaults={'elo_rating': 1000},
        )
        serializer = ArenaStatsSerializer(stats)
        return Response(serializer.data)


class ArenaLeaderboardView(views.APIView):
    """Arena ELO leaderboard."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 100)

        top_players = PlayerArenaStats.objects.filter(
            matches_played__gte=3,
        ).select_related('player').order_by('-elo_rating')[:limit]

        leaderboard = []
        for i, stats in enumerate(top_players, 1):
            leaderboard.append({
                'rank': i,
                'display_name': stats.player.display_name,
                'elo_rating': stats.elo_rating,
                'matches_played': stats.matches_played,
                'matches_won': stats.matches_won,
                'win_streak': stats.win_streak,
            })

        # Get requesting player's rank
        player_stats, _ = PlayerArenaStats.objects.get_or_create(
            player=request.user.player,
            defaults={'elo_rating': 1000},
        )
        player_rank = PlayerArenaStats.objects.filter(
            matches_played__gte=3,
            elo_rating__gt=player_stats.elo_rating,
        ).count() + 1

        return Response({
            'leaderboard': leaderboard,
            'player_rank': player_rank if player_stats.matches_played >= 3 else None,
            'player_stats': ArenaStatsSerializer(player_stats).data,
        })
