from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Player
from .friends_models import FriendRequest, Friendship
from .friends_serializers import (
    FriendSerializer,
    FriendRequestSerializer,
    SendFriendRequestSerializer,
    RespondFriendRequestSerializer,
)


class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        friendships = Friendship.objects.filter(
            Q(player1=player) | Q(player2=player)
        ).select_related('player1', 'player2')

        friends = []
        for friendship in friendships:
            friend = friendship.player2 if friendship.player1_id == player.id else friendship.player1
            friends.append(friend)

        serializer = FriendSerializer(friends, many=True)
        return Response({'friends': serializer.data})


class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendFriendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        player = request.user.player
        target_id = serializer.validated_data['player_id']
        message = serializer.validated_data.get('message', '')

        # Can't send to self
        if target_id == player.id:
            return Response(
                {'detail': 'You cannot send a friend request to yourself.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check target exists
        try:
            target = Player.objects.get(id=target_id)
        except Player.DoesNotExist:
            return Response(
                {'detail': 'Player not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check no existing friendship
        p1, p2 = (player, target) if player.id < target.id else (target, player)
        if Friendship.objects.filter(player1=p1, player2=p2).exists():
            return Response(
                {'detail': 'You are already friends with this player.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check no duplicate pending request (either direction)
        if FriendRequest.objects.filter(
            from_player=player, to_player=target, status='pending'
        ).exists():
            return Response(
                {'detail': 'You already have a pending friend request to this player.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if FriendRequest.objects.filter(
            from_player=target, to_player=player, status='pending'
        ).exists():
            return Response(
                {'detail': 'This player has already sent you a friend request. Check your requests.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friend_request = FriendRequest.objects.create(
            from_player=player,
            to_player=target,
            message=message,
            status='pending',
        )

        from apps.notifications.services import NotificationService
        NotificationService.send_friend_request(target, player)

        return Response(
            FriendRequestSerializer(friend_request).data,
            status=status.HTTP_201_CREATED,
        )


class FriendRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        pending_requests = FriendRequest.objects.filter(
            to_player=player, status='pending'
        ).select_related('from_player')

        serializer = FriendRequestSerializer(pending_requests, many=True)
        return Response({'requests': serializer.data})


class RespondFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RespondFriendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        player = request.user.player
        request_id = serializer.validated_data['request_id']
        action = serializer.validated_data['action']

        try:
            friend_request = FriendRequest.objects.get(
                id=request_id, to_player=player, status='pending'
            )
        except FriendRequest.DoesNotExist:
            return Response(
                {'detail': 'Friend request not found or already responded to.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if action == 'accept':
            friend_request.status = 'accepted'
            friend_request.responded_at = timezone.now()
            friend_request.save()

            # Create friendship ensuring player1.id < player2.id
            p1 = friend_request.from_player
            p2 = friend_request.to_player
            if p1.id > p2.id:
                p1, p2 = p2, p1

            Friendship.objects.get_or_create(player1=p1, player2=p2)

        elif action == 'reject':
            friend_request.status = 'rejected'
            friend_request.responded_at = timezone.now()
            friend_request.save()

        return Response(FriendRequestSerializer(friend_request).data)


class RemoveFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, player_id):
        player = request.user.player

        # Ensure consistent ordering for lookup
        p1_id, p2_id = (player.id, player_id) if player.id < player_id else (player_id, player.id)

        deleted_count, _ = Friendship.objects.filter(
            player1_id=p1_id, player2_id=p2_id
        ).delete()

        if deleted_count == 0:
            return Response(
                {'detail': 'Friendship not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {'detail': 'Friend removed successfully.'},
            status=status.HTTP_200_OK,
        )
