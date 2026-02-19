from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import PersonalityAssessment
from .serializers import AssessmentSubmitSerializer, PersonalityAssessmentSerializer
from .services import AssessmentScoringService


class AssessmentQuestionsView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import json
        from pathlib import Path
        questions_path = Path(__file__).parent / 'data' / 'questions_en.json'
        if questions_path.exists():
            with open(questions_path) as f:
                questions = json.load(f)
        else:
            questions = []
        return Response({'questions': questions, 'total': len(questions)})


class AssessmentSubmitView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AssessmentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = AssessmentScoringService.process_assessment(
            player=request.user.player,
            answers=serializer.validated_data['answers'],
        )
        return Response(result, status=status.HTTP_200_OK)


class AssessmentResultView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            assessment = request.user.player.assessment
        except PersonalityAssessment.DoesNotExist:
            return Response({'detail': 'No assessment found.'}, status=status.HTTP_404_NOT_FOUND)

        traits = PersonalityAssessmentSerializer(assessment).data
        realm_scores = AssessmentScoringService.calculate_realm_scores(traits)
        return Response({
            'traits': traits,
            'realm_scores': realm_scores,
        })
