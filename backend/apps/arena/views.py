"""Arena views — Phase 2 stub."""
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ArenaStatusView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'status': 'coming_soon',
            'message': 'The Arena is being prepared. Stay tuned for competitive challenges!',
        })
