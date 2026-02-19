from django.urls import path
from . import views

urlpatterns = [
    path('questions/', views.AssessmentQuestionsView.as_view(), name='assessment-questions'),
    path('submit/', views.AssessmentSubmitView.as_view(), name='assessment-submit'),
    path('result/', views.AssessmentResultView.as_view(), name='assessment-result'),
]
