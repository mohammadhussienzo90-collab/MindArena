"""
AI Engine API Views
====================
12 API endpoints exposing the AI engine to the frontend.
All views require JWT authentication (IsAuthenticated).
"""
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_engine.models import (
    KnowledgeState,
    LearningPath,
    PlayerAbility,
    PlayerEngagement,
    SpacedRepetitionCard,
)
from apps.ai_engine.orchestrator import AIOrchestrator
from apps.ai_engine.serializers import (
    EngagementSerializer,
    KnowledgeStateSerializer,
    LearningPathDetailSerializer,
    LearningPathSerializer,
    NextChallengeSerializer,
    PlayerAbilitySerializer,
    PlayerInsightsSerializer,
    RecommendationSerializer,
    SessionEndRequestSerializer,
    SessionEndResponseSerializer,
    SessionStartResponseSerializer,
    SmartChatRequestSerializer,
    SmartChatResponseSerializer,
    SRSCardSerializer,
    WeeklyPlanDaySerializer,
)

logger = logging.getLogger(__name__)


# ======================================================================
# 1. Player Insights (GET)
# ======================================================================

class PlayerInsightsView(APIView):
    """Comprehensive AI-driven player insights for the dashboard.

    Returns knowledge radar, flow state, engagement metrics, churn risk,
    recommended challenges, learning path, abilities, SRS summary,
    skill gaps, and player type classification.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        insights = AIOrchestrator.get_player_insights(player)
        serializer = PlayerInsightsSerializer(insights)
        return Response(serializer.data)


# ======================================================================
# 2. Next Challenge (GET)
# ======================================================================

class NextChallengeView(APIView):
    """Get the AI-recommended next challenge for the player.

    Query Parameters
    ----------------
    realm : str, optional
        Realm slug to filter recommendations.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        realm_slug = request.query_params.get('realm', None)

        recommendation = AIOrchestrator.get_next_challenge(player, realm_slug=realm_slug)

        if recommendation is None:
            return Response(
                {'detail': 'No challenges available for recommendation.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = NextChallengeSerializer(recommendation)
        return Response(serializer.data)


# ======================================================================
# 3. Learning Path (GET)
# ======================================================================

class LearningPathView(APIView):
    """Generate a personalised learning path based on skill prerequisites
    and current mastery levels.

    Returns an ordered list of skills to focus on, with priority,
    current mastery, target mastery, prerequisites, and dependants.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.ai_engine.algorithms.learning_path import generate_learning_path

        player = request.user.player
        path = generate_learning_path(player)

        # Also persist/update the LearningPath model
        if path:
            lp, created = LearningPath.objects.get_or_create(
                player=player,
                defaults={
                    'current_focus_skill': path[0]['skill'] if path else '',
                    'skill_sequence': [step['skill'] for step in path],
                },
            )
            if not created:
                lp.current_focus_skill = path[0]['skill'] if path else ''
                lp.skill_sequence = [step['skill'] for step in path]
                lp.path_version += 1
                lp.save()

        serializer = LearningPathDetailSerializer(path, many=True)
        return Response(serializer.data)


# ======================================================================
# 4. Weekly Plan (GET)
# ======================================================================

class WeeklyPlanView(APIView):
    """Generate a 7-day learning plan with daily challenge assignments.

    Distributes focus skills across the week, includes review challenges,
    and adapts to the player's current mastery levels.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.ai_engine.algorithms.learning_path import generate_weekly_plan

        player = request.user.player
        plan = generate_weekly_plan(player)

        # Persist to LearningPath model
        lp, created = LearningPath.objects.get_or_create(
            player=player,
            defaults={'weekly_plan': plan},
        )
        if not created:
            lp.weekly_plan = plan
            lp.save()

        serializer = WeeklyPlanDaySerializer(plan, many=True)
        return Response(serializer.data)


# ======================================================================
# 5. Recommendations (GET)
# ======================================================================

class RecommendationsView(APIView):
    """Get a list of AI-recommended challenges.

    Query Parameters
    ----------------
    n : int, optional
        Number of recommendations (default: 5, max: 20).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.ai_engine.algorithms.recommender import hybrid_recommend
        from apps.ai_engine.models import RecommendationLog

        player = request.user.player

        n = request.query_params.get('n', 5)
        try:
            n = min(int(n), 20)
        except (ValueError, TypeError):
            n = 5

        recommendations = hybrid_recommend(player, n=n)

        # Log recommendations
        for rec in recommendations:
            RecommendationLog.objects.create(
                player=player,
                challenge=rec['challenge'],
                recommendation_source='hybrid',
                score=rec['composite_score'],
            )

        # Serialize
        result = []
        for rec in recommendations:
            challenge = rec['challenge']
            result.append({
                'challenge_id': challenge.id,
                'title': challenge.title_en,
                'challenge_type': challenge.challenge_type,
                'difficulty': challenge.difficulty,
                'primary_trait': challenge.primary_trait,
                'realm_slug': (
                    challenge.quest.realm.slug
                    if challenge.quest and challenge.quest.realm
                    else None
                ),
                'composite_score': rec['composite_score'],
                'signals': rec['signals'],
            })

        serializer = RecommendationSerializer(result, many=True)
        return Response(serializer.data)


# ======================================================================
# 6. Knowledge State (GET)
# ======================================================================

class KnowledgeStateView(APIView):
    """Return all BKT knowledge states for the authenticated player.

    Returns per-skill mastery probability, observation count,
    mastered status, and expected correct probability.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        states = KnowledgeState.objects.filter(player=player).order_by('skill')
        serializer = KnowledgeStateSerializer(states, many=True)
        return Response(serializer.data)


# ======================================================================
# 7. SRS Due Cards (GET)
# ======================================================================

class SRSDueView(APIView):
    """Return SpacedRepetitionCards where due_date <= now.

    These are the challenges the player should review today according
    to the FSRS scheduling algorithm.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        now = timezone.now()

        due_cards = (
            SpacedRepetitionCard.objects
            .filter(player=player, due_date__lte=now)
            .select_related('challenge')
            .order_by('due_date')
        )

        serializer = SRSCardSerializer(due_cards, many=True)
        return Response(serializer.data)


# ======================================================================
# 8. Engagement (GET)
# ======================================================================

class EngagementView(APIView):
    """Return or create the player's engagement metrics.

    If no engagement record exists, computes fresh engagement and churn
    scores from behavioral data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.ai_engine.algorithms.behavior import BehaviorEngine

        player = request.user.player

        engagement, created = PlayerEngagement.objects.get_or_create(
            player=player,
            defaults={
                'engagement_score': 0.5,
                'churn_risk': 0.5,
            },
        )

        if created:
            # Compute fresh metrics
            engagement.engagement_score = BehaviorEngine.calculate_engagement_score(player)
            engagement.churn_risk = BehaviorEngine.predict_churn(player)
            engagement.personality_cluster = BehaviorEngine.classify_player_type(player)
            engagement.save()

        serializer = EngagementSerializer(engagement)
        return Response(serializer.data)


# ======================================================================
# 9. Smart Chat (POST)
# ======================================================================

class SmartChatView(APIView):
    """Smart Noor companion chat endpoint.

    Accepts a player message and optional context, returns a contextual
    response with detected emotion, coaching strategy, and suggestions.
    No external API calls are made -- all logic is rule-based.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SmartChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        player = request.user.player
        message = serializer.validated_data['message']
        context = serializer.validated_data.get('context', {})

        result = AIOrchestrator.companion_chat(player, message, context)

        response_serializer = SmartChatResponseSerializer(result)
        return Response(response_serializer.data)


# ======================================================================
# 10. Session Start (POST)
# ======================================================================

class SessionStartView(APIView):
    """Start a new AI-monitored play session.

    Creates a PlayerSession record and returns the session ID.
    The client should call session/end/ when the player leaves.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        player = request.user.player
        session_id = AIOrchestrator.on_session_start(player)

        from apps.ai_engine.models import PlayerSession

        session = PlayerSession.objects.get(id=session_id)

        serializer = SessionStartResponseSerializer({
            'session_id': session.id,
            'started_at': session.started_at,
        })
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ======================================================================
# 11. Session End (POST)
# ======================================================================

class SessionEndView(APIView):
    """End an AI-monitored play session.

    Computes session-level analytics: flow score, inferred emotion,
    engagement update, and churn risk.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SessionEndRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        player = request.user.player
        session_id = serializer.validated_data['session_id']

        result = AIOrchestrator.on_session_end(player, session_id)

        if 'error' in result:
            return Response(
                {'detail': result['error']},
                status=status.HTTP_404_NOT_FOUND,
            )

        response_serializer = SessionEndResponseSerializer(result)
        return Response(response_serializer.data)


# ======================================================================
# 12. Difficulty / Abilities (GET)
# ======================================================================

class DifficultyView(APIView):
    """Return all IRT ability (theta) estimates for the player.

    Each entry represents the player's estimated ability level for a
    specific skill/realm combination, along with the standard error
    and response count.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        player = request.user.player
        abilities = (
            PlayerAbility.objects
            .filter(player=player)
            .select_related('realm')
            .order_by('skill')
        )
        serializer = PlayerAbilitySerializer(abilities, many=True)
        return Response(serializer.data)
