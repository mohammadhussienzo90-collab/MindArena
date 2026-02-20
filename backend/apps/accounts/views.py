from rest_framework import status
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
