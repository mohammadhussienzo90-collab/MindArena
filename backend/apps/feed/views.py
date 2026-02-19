from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FeedItem
from .serializers import FeedItemSerializer, FeedInteractionSerializer
from .services import FeedService


class FeedListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        items = FeedService.get_personalized_feed(request.user.player, page=page)
        return Response(FeedItemSerializer(items, many=True).data)


class FeedInteractView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        try:
            item = FeedItem.objects.get(id=item_id, is_active=True)
        except FeedItem.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FeedInteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        FeedService.mark_interaction(
            player=request.user.player,
            feed_item=item,
            **serializer.validated_data,
        )
        return Response({'status': 'ok'})
