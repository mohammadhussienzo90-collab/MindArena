from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.core.throttles import AuthRateThrottle
from . import views


class ThrottledLoginView(TokenObtainPairView):
    throttle_classes = [AuthRateThrottle]


urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', ThrottledLoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.PlayerProfileView.as_view(), name='profile'),
]
