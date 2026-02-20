from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.core.pagination import StandardPagination
from .models import Notification
from .serializers import NotificationSerializer, NotificationMarkReadSerializer


class NotificationListView(views.APIView):
    """List notifications for the authenticated player."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        queryset = Notification.objects.filter(recipient=player)

        # Optional filter: only unread
        unread_only = request.query_params.get('unread_only', '').lower()
        if unread_only in ('true', '1', 'yes'):
            queryset = queryset.filter(is_read=False)

        unread_count = Notification.objects.filter(
            recipient=player, is_read=False,
        ).count()

        # Paginate
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = NotificationSerializer(page, many=True)

        return Response({
            'unread_count': unread_count,
            'results': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
        })


class NotificationMarkReadView(views.APIView):
    """Mark notifications as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        player = request.user.player
        mark_all = request.data.get('mark_all', False)

        if mark_all:
            updated = Notification.objects.filter(
                recipient=player, is_read=False,
            ).update(is_read=True)
        else:
            serializer = NotificationMarkReadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            notification_ids = serializer.validated_data['notification_ids']

            updated = Notification.objects.filter(
                recipient=player,
                id__in=notification_ids,
                is_read=False,
            ).update(is_read=True)

        return Response({'updated': updated})


class NotificationDeleteView(views.APIView):
    """Delete a single notification belonging to the authenticated player."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):
        player = request.user.player

        try:
            notification = Notification.objects.get(
                id=notification_id, recipient=player,
            )
        except Notification.DoesNotExist:
            return Response(
                {'detail': 'Notification not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
