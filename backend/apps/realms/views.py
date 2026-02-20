from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Realm, Quest, Challenge
from .serializers import (
    RealmListSerializer, RealmDetailSerializer,
    QuestListSerializer, QuestDetailSerializer,
    ChallengeSerializer, ChallengeSubmitSerializer,
)
from .services import validate_challenge_answer


class RealmViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Realm.objects.filter(is_active=True)
    lookup_field = 'slug'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RealmDetailSerializer
        return RealmListSerializer

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def challenges(self, request, slug=None):
        """List challenges for a specific realm: GET /realms/{slug}/challenges/"""
        realm = self.get_object()
        challenges = Challenge.objects.filter(
            quest__realm=realm, is_active=True,
        ).select_related('quest')
        return Response(ChallengeSerializer(challenges, many=True).data)


class QuestViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        realm_slug = self.kwargs.get('realm_slug')
        if realm_slug:
            return Quest.objects.filter(realm__slug=realm_slug, is_active=True)
        return Quest.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuestDetailSerializer
        return QuestListSerializer

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        quest = self.get_object()
        from apps.progression.models import PlayerQuestProgress
        progress, created = PlayerQuestProgress.objects.get_or_create(
            player=request.user.player,
            quest=quest,
            defaults={
                'status': 'in_progress',
                'challenges_total': quest.challenges.count(),
            }
        )
        if not created and progress.status == 'locked':
            progress.status = 'in_progress'
            progress.save()
        return Response({'status': progress.status, 'challenges_total': progress.challenges_total})


class ChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Challenge.objects.filter(is_active=True)
    serializer_class = ChallengeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        challenge = self.get_object()
        serializer = ChallengeSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = validate_challenge_answer(
            challenge,
            serializer.validated_data['answer_data'],
            serializer.validated_data['time_taken_secs'],
        )

        # Award XP via progression service
        from apps.progression.services import XPService
        xp_earned = result['base_xp']
        if result.get('bonus'):
            xp_earned += result['bonus_xp']

        XPService.award_xp(
            player=request.user.player,
            amount=xp_earned,
            source='challenge',
            source_id=challenge.id,
            realm=challenge.quest.realm,
        )

        # Record result
        from apps.progression.models import PlayerChallengeResult, PlayerRealmStat, PlayerQuestProgress
        PlayerChallengeResult.objects.create(
            player=request.user.player,
            challenge=challenge,
            score=result['score'],
            is_correct=result['is_correct'],
            time_taken_secs=serializer.validated_data['time_taken_secs'],
            answer_data=serializer.validated_data['answer_data'],
            xp_earned=xp_earned,
        )

        # Update realm stat counters
        if result['is_correct']:
            realm_stat, _ = PlayerRealmStat.objects.get_or_create(
                player=request.user.player,
                realm=challenge.quest.realm,
            )
            realm_stat.challenges_completed += 1
            update_fields = ['challenges_completed']
            if result['score'] == 100:
                realm_stat.challenges_perfect += 1
                update_fields.append('challenges_perfect')
            realm_stat.save(update_fields=update_fields)

            # Update quest progress
            quest_progress = PlayerQuestProgress.objects.filter(
                player=request.user.player,
                quest=challenge.quest,
                status='in_progress',
            ).first()
            if quest_progress:
                quest_progress.challenges_completed += 1
                if quest_progress.challenges_completed >= quest_progress.challenges_total:
                    quest_progress.status = 'completed'
                    quest_progress.completed_at = timezone.now()
                quest_progress.save()

        # Check for newly earned achievements
        from apps.progression.achievement_checker import AchievementChecker
        new_achievements = AchievementChecker.check_specific(
            request.user.player, 'challenge_completed',
        )
        if new_achievements:
            result['new_achievements'] = new_achievements

        return Response(result)
