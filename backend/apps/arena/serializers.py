"""Serializers for the Arena app — competitive matchmaking system."""
from rest_framework import serializers

from apps.arena.models import (
    ArenaMatch,
    ArenaMatchParticipant,
    ArenaRoundResult,
    PlayerArenaStats,
)


# ---------------------------------------------------------------------------
# Read serializers
# ---------------------------------------------------------------------------

class ArenaParticipantSerializer(serializers.ModelSerializer):
    """Serializes participant info within a match."""

    display_name = serializers.CharField(source='player.display_name', read_only=True)
    avatar_preset = serializers.CharField(source='player.avatar_preset', read_only=True)

    class Meta:
        model = ArenaMatchParticipant
        fields = [
            'id',
            'display_name',
            'avatar_preset',
            'score',
            'correct_answers',
            'total_time_secs',
            'is_ready',
            'joined_at',
        ]
        read_only_fields = fields


class ArenaRoundResultSerializer(serializers.ModelSerializer):
    """Serializes a single round result for a participant."""

    challenge_slug = serializers.CharField(source='challenge.slug', read_only=True)
    challenge_title = serializers.CharField(source='challenge.title_en', read_only=True)
    participant_name = serializers.CharField(
        source='participant.player.display_name', read_only=True
    )

    class Meta:
        model = ArenaRoundResult
        fields = [
            'id',
            'round_number',
            'challenge_slug',
            'challenge_title',
            'participant_name',
            'is_correct',
            'time_taken_secs',
            'score_earned',
            'created_at',
        ]
        read_only_fields = fields


class ArenaMatchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing arena matches."""

    realm_slug = serializers.CharField(source='realm.slug', read_only=True, default=None)
    realm_name = serializers.CharField(source='realm.name_en', read_only=True, default=None)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = ArenaMatch
        fields = [
            'id',
            'match_type',
            'realm_slug',
            'realm_name',
            'status',
            'max_players',
            'participant_count',
            'created_at',
        ]
        read_only_fields = fields

    def get_participant_count(self, obj):
        """Return the number of participants currently in the match."""
        if hasattr(obj, '_participant_count'):
            # Allow annotated querysets to avoid extra queries
            return obj._participant_count
        return obj.participants.count()


class ArenaMatchDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for a single arena match."""

    realm_slug = serializers.CharField(source='realm.slug', read_only=True, default=None)
    realm_name = serializers.CharField(source='realm.name_en', read_only=True, default=None)
    participants = ArenaParticipantSerializer(many=True, read_only=True)
    winner_name = serializers.CharField(
        source='winner.display_name', read_only=True, default=None
    )
    rounds = serializers.SerializerMethodField()

    class Meta:
        model = ArenaMatch
        fields = [
            'id',
            'match_type',
            'realm_slug',
            'realm_name',
            'status',
            'max_players',
            'current_round',
            'total_rounds',
            'challenge_pool',
            'winner_name',
            'elo_change',
            'started_at',
            'finished_at',
            'created_at',
            'is_active',
            'participants',
            'rounds',
        ]
        read_only_fields = fields

    def get_rounds(self, obj):
        """Return all round results grouped by round number."""
        results = ArenaRoundResult.objects.filter(
            match=obj
        ).select_related(
            'participant__player', 'challenge'
        ).order_by('round_number', 'created_at')
        return ArenaRoundResultSerializer(results, many=True).data


class ArenaStatsSerializer(serializers.ModelSerializer):
    """Serializes player arena statistics."""

    display_name = serializers.CharField(source='player.display_name', read_only=True)
    win_rate = serializers.SerializerMethodField()
    accuracy = serializers.SerializerMethodField()

    class Meta:
        model = PlayerArenaStats
        fields = [
            'display_name',
            'elo_rating',
            'matches_played',
            'matches_won',
            'matches_lost',
            'win_streak',
            'best_win_streak',
            'total_correct',
            'total_questions',
            'win_rate',
            'accuracy',
            'last_match_at',
        ]
        read_only_fields = fields

    def get_win_rate(self, obj):
        """Return win rate as a percentage (0-100)."""
        if obj.matches_played == 0:
            return 0.0
        return round((obj.matches_won / obj.matches_played) * 100, 1)

    def get_accuracy(self, obj):
        """Return answer accuracy as a percentage (0-100)."""
        if obj.total_questions == 0:
            return 0.0
        return round((obj.total_correct / obj.total_questions) * 100, 1)


# ---------------------------------------------------------------------------
# Write / input serializers
# ---------------------------------------------------------------------------

class ArenaMatchCreateSerializer(serializers.Serializer):
    """Input serializer for creating a new arena match."""

    MATCH_TYPE_CHOICES = ['speed', 'strategic', 'team']

    match_type = serializers.ChoiceField(choices=[
        ('speed', 'Speed Duel'),
        ('strategic', 'Strategic Battle'),
        ('team', 'Team Arena'),
    ])
    realm_slug = serializers.SlugField(max_length=50)
    total_rounds = serializers.IntegerField(min_value=1, max_value=20, default=5)

    def validate_realm_slug(self, value):
        """Ensure the realm exists and is active."""
        from apps.realms.models import Realm

        try:
            realm = Realm.objects.get(slug=value, is_active=True)
        except Realm.DoesNotExist:
            raise serializers.ValidationError(
                f"No active realm found with slug '{value}'."
            )
        # Verify enough challenges exist in this realm
        challenge_count = realm.quests.filter(
            is_active=True
        ).values('challenges').count()
        # Store realm on the serializer for use in the view/service
        self._realm = realm
        return value


class ArenaSubmitAnswerSerializer(serializers.Serializer):
    """Input serializer for submitting an answer during a live match."""

    match_id = serializers.IntegerField()
    round_number = serializers.IntegerField(min_value=1)
    challenge_id = serializers.IntegerField()
    answer = serializers.JSONField()
    time_taken_secs = serializers.FloatField(min_value=0, max_value=600)

    def validate_match_id(self, value):
        """Ensure the match exists."""
        try:
            ArenaMatch.objects.get(id=value)
        except ArenaMatch.DoesNotExist:
            raise serializers.ValidationError(
                f"Match with id {value} does not exist."
            )
        return value

    def validate(self, attrs):
        """Cross-field validation: match must be in progress and round must match."""
        match = ArenaMatch.objects.get(id=attrs['match_id'])
        if match.status != 'in_progress':
            raise serializers.ValidationError(
                {'match_id': 'This match is not currently in progress.'}
            )
        if match.current_round != attrs['round_number']:
            raise serializers.ValidationError(
                {'round_number': (
                    f"Expected round {match.current_round}, "
                    f"got {attrs['round_number']}."
                )}
            )
        return attrs
