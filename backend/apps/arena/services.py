"""Arena service layer — matchmaking, scoring, and ELO calculations."""
import math
import random

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.arena.models import (
    ArenaMatch,
    ArenaMatchParticipant,
    ArenaRoundResult,
    PlayerArenaStats,
)
from apps.realms.models import Challenge, Realm


class ArenaService:
    """Stateless service class for all arena match operations."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    @transaction.atomic
    def create_match(player, match_type, realm_slug, total_rounds=5):
        """Create a new arena match and add the creating player as first participant.

        Args:
            player: Player instance who is creating the match.
            match_type: One of 'speed', 'strategic', 'team'.
            realm_slug: Slug of the realm to draw challenges from.
            total_rounds: Number of rounds in the match (default 5).

        Returns:
            The newly created ArenaMatch instance.
        """
        realm = Realm.objects.get(slug=realm_slug, is_active=True)

        # Gather eligible challenges from this realm's active quests
        challenges = list(
            Challenge.objects.filter(
                quest__realm=realm,
                quest__is_active=True,
                is_active=True,
            ).values_list('id', flat=True)
        )

        if len(challenges) < total_rounds:
            raise ValueError(
                f"Realm '{realm_slug}' only has {len(challenges)} active "
                f"challenges but {total_rounds} rounds were requested."
            )

        # Randomly select challenges for the match
        selected_ids = random.sample(challenges, total_rounds)

        # Determine max players based on match type
        max_players_map = {
            'speed': 2,
            'strategic': 2,
            'team': 4,
        }

        match = ArenaMatch.objects.create(
            match_type=match_type,
            realm=realm,
            status='waiting',
            max_players=max_players_map.get(match_type, 2),
            current_round=0,
            total_rounds=total_rounds,
            challenge_pool=selected_ids,
            elo_change=0,
        )

        # Add the creating player as the first participant
        ArenaMatchParticipant.objects.create(
            match=match,
            player=player,
            score=0,
            correct_answers=0,
            total_time_secs=0.0,
            is_ready=True,
        )

        # Ensure the player has arena stats
        PlayerArenaStats.objects.get_or_create(
            player=player,
            defaults={
                'elo_rating': 1000,
                'matches_played': 0,
                'matches_won': 0,
                'matches_lost': 0,
                'win_streak': 0,
                'best_win_streak': 0,
                'total_correct': 0,
                'total_questions': 0,
            },
        )

        return match

    @staticmethod
    @transaction.atomic
    def join_match(player, match_id):
        """Join an existing waiting match.

        Args:
            player: Player instance joining the match.
            match_id: ID of the match to join.

        Returns:
            The ArenaMatch instance (possibly now in_progress).

        Raises:
            ValueError: If the match is not joinable.
        """
        match = ArenaMatch.objects.select_for_update().get(id=match_id)

        if match.status != 'waiting':
            raise ValueError("This match is no longer accepting players.")

        current_count = match.participants.count()
        if current_count >= match.max_players:
            raise ValueError("This match is already full.")

        # Check player is not already in the match
        if match.participants.filter(player=player).exists():
            raise ValueError("You have already joined this match.")

        ArenaMatchParticipant.objects.create(
            match=match,
            player=player,
            score=0,
            correct_answers=0,
            total_time_secs=0.0,
            is_ready=True,
        )

        # Ensure the player has arena stats
        PlayerArenaStats.objects.get_or_create(
            player=player,
            defaults={
                'elo_rating': 1000,
                'matches_played': 0,
                'matches_won': 0,
                'matches_lost': 0,
                'win_streak': 0,
                'best_win_streak': 0,
                'total_correct': 0,
                'total_questions': 0,
            },
        )

        # If the match is now full, start it
        new_count = match.participants.count()
        if new_count >= match.max_players:
            match.status = 'in_progress'
            match.started_at = timezone.now()
            match.current_round = 1
            match.save(update_fields=['status', 'started_at', 'current_round'])

        return match

    @staticmethod
    def get_current_challenge(match):
        """Return the Challenge object for the match's current round.

        Args:
            match: ArenaMatch instance.

        Returns:
            Challenge instance for the current round.

        Raises:
            ValueError: If the match has no current round or pool is invalid.
        """
        if not match.challenge_pool or match.current_round < 1:
            raise ValueError("Match has no active round.")

        index = match.current_round - 1
        if index >= len(match.challenge_pool):
            raise ValueError(
                f"Round {match.current_round} exceeds challenge pool size "
                f"({len(match.challenge_pool)})."
            )

        challenge_id = match.challenge_pool[index]
        return Challenge.objects.get(id=challenge_id)

    @staticmethod
    @transaction.atomic
    def submit_answer(player, match_id, round_number, challenge_id, answer, time_taken_secs):
        """Submit an answer for a round in an active match.

        Args:
            player: Player instance submitting the answer.
            match_id: ID of the match.
            round_number: Current round number (must match match.current_round).
            challenge_id: ID of the challenge being answered.
            answer: The player's answer (JSON-compatible value).
            time_taken_secs: Time the player took to answer.

        Returns:
            dict with round result information.

        Raises:
            ValueError: If the submission is invalid.
        """
        match = ArenaMatch.objects.select_for_update().get(id=match_id)

        if match.status != 'in_progress':
            raise ValueError("This match is not in progress.")

        if match.current_round != round_number:
            raise ValueError(
                f"Expected round {match.current_round}, got {round_number}."
            )

        participant = ArenaMatchParticipant.objects.get(
            match=match, player=player,
        )

        # Prevent double submission for same round
        already_submitted = ArenaRoundResult.objects.filter(
            match=match,
            participant=participant,
            round_number=round_number,
        ).exists()
        if already_submitted:
            raise ValueError(
                f"You have already submitted an answer for round {round_number}."
            )

        challenge = Challenge.objects.get(id=challenge_id)

        # Verify this is the correct challenge for this round
        expected_challenge_id = match.challenge_pool[round_number - 1]
        if challenge.id != expected_challenge_id:
            raise ValueError("Challenge does not match the current round.")

        # Check the answer
        correct_answer = challenge.content.get('correct_answer')
        is_correct = (answer == correct_answer)

        # Calculate score
        score_earned = 0
        if is_correct:
            # Base score for a correct answer
            score_earned = 100

            # Time bonus: up to 50 extra points if answered quickly
            time_limit = challenge.time_limit_secs or 30  # default 30s
            if time_taken_secs < time_limit:
                # Linear bonus: faster answer = more bonus
                time_ratio = 1.0 - (time_taken_secs / time_limit)
                time_bonus = int(50 * time_ratio)
                score_earned += time_bonus

        # Create the round result
        round_result = ArenaRoundResult.objects.create(
            match=match,
            participant=participant,
            round_number=round_number,
            challenge=challenge,
            is_correct=is_correct,
            time_taken_secs=time_taken_secs,
            score_earned=score_earned,
        )

        # Update participant running totals
        participant.score += score_earned
        participant.total_time_secs += time_taken_secs
        if is_correct:
            participant.correct_answers += 1
        participant.save(update_fields=['score', 'correct_answers', 'total_time_secs'])

        # Check if all participants have submitted for this round
        participant_count = match.participants.count()
        submissions_this_round = ArenaRoundResult.objects.filter(
            match=match, round_number=round_number,
        ).count()

        if submissions_this_round >= participant_count:
            ArenaService._advance_round(match)

        return {
            'round_number': round_number,
            'challenge_id': challenge.id,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'score_earned': score_earned,
            'time_taken_secs': time_taken_secs,
            'participant_total_score': participant.score,
        }

    @staticmethod
    def find_match(player, match_type=None, realm_slug=None):
        """Find an open match for the player to join.

        Args:
            player: Player instance looking for a match.
            match_type: Optional filter by match type.
            realm_slug: Optional filter by realm slug.

        Returns:
            ArenaMatch instance or None if no suitable match found.
        """
        queryset = ArenaMatch.objects.filter(
            status='waiting',
            is_active=True,
        ).exclude(
            participants__player=player,
        )

        if match_type:
            queryset = queryset.filter(match_type=match_type)

        if realm_slug:
            queryset = queryset.filter(realm__slug=realm_slug)

        # Prefer matches closest to starting (most participants), then oldest
        match = queryset.annotate(
            participant_count=Count('participants'),
        ).order_by('-participant_count', 'created_at').first()

        return match

    # ------------------------------------------------------------------
    # ELO calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_elo(winner_rating, loser_rating, k=32):
        """Calculate new ELO ratings after a match.

        Uses the standard ELO formula:
            E_a = 1 / (1 + 10^((R_b - R_a) / 400))
            new_R_a = R_a + K * (1 - E_a)     (winner)
            new_R_b = R_b + K * (0 - E_b)     (loser)

        Args:
            winner_rating: Current ELO rating of the winner.
            loser_rating: Current ELO rating of the loser.
            k: K-factor (default 32).

        Returns:
            Tuple of (winner_new_rating, loser_new_rating, change_amount).
        """
        expected_winner = 1.0 / (
            1.0 + math.pow(10, (loser_rating - winner_rating) / 400.0)
        )
        expected_loser = 1.0 / (
            1.0 + math.pow(10, (winner_rating - loser_rating) / 400.0)
        )

        change = round(k * (1 - expected_winner))

        winner_new = winner_rating + change
        loser_new = max(0, loser_rating - change)  # never go below 0

        return winner_new, loser_new, change

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _advance_round(match):
        """Advance the match to the next round, or finish it.

        Args:
            match: ArenaMatch instance (must already be locked for update).
        """
        next_round = match.current_round + 1

        if next_round > match.total_rounds:
            ArenaService._finish_match(match)
        else:
            match.current_round = next_round
            match.save(update_fields=['current_round'])

    @staticmethod
    @transaction.atomic
    def _finish_match(match):
        """Finish the match: determine winner, update ELO, update stats.

        Args:
            match: ArenaMatch instance (must already be locked for update).

        Returns:
            The updated ArenaMatch instance.
        """
        # Determine the winner (highest total score)
        participants = list(
            match.participants.select_related('player').order_by('-score')
        )

        if not participants:
            match.status = 'cancelled'
            match.finished_at = timezone.now()
            match.save(update_fields=['status', 'finished_at'])
            return match

        winner_participant = participants[0]

        # Handle ties: first to finish (lowest total_time_secs) wins
        tied = [p for p in participants if p.score == winner_participant.score]
        if len(tied) > 1:
            winner_participant = min(tied, key=lambda p: p.total_time_secs)

        match.status = 'completed'
        match.winner = winner_participant.player
        match.finished_at = timezone.now()

        # Calculate and apply ELO changes for each pair
        # For 2-player matches, straightforward ELO update
        elo_change_total = 0

        if len(participants) == 2:
            winner = winner_participant
            loser = [p for p in participants if p.id != winner.id][0]

            winner_stats, _ = PlayerArenaStats.objects.get_or_create(
                player=winner.player,
                defaults={
                    'elo_rating': 1000,
                    'matches_played': 0,
                    'matches_won': 0,
                    'matches_lost': 0,
                    'win_streak': 0,
                    'best_win_streak': 0,
                    'total_correct': 0,
                    'total_questions': 0,
                },
            )
            loser_stats, _ = PlayerArenaStats.objects.get_or_create(
                player=loser.player,
                defaults={
                    'elo_rating': 1000,
                    'matches_played': 0,
                    'matches_won': 0,
                    'matches_lost': 0,
                    'win_streak': 0,
                    'best_win_streak': 0,
                    'total_correct': 0,
                    'total_questions': 0,
                },
            )

            new_winner_elo, new_loser_elo, change = ArenaService.calculate_elo(
                winner_stats.elo_rating, loser_stats.elo_rating,
            )

            # Update winner stats
            winner_stats.elo_rating = new_winner_elo
            winner_stats.matches_played += 1
            winner_stats.matches_won += 1
            winner_stats.win_streak += 1
            winner_stats.best_win_streak = max(
                winner_stats.best_win_streak, winner_stats.win_streak
            )
            winner_stats.total_correct += winner.correct_answers
            winner_stats.total_questions += match.total_rounds
            winner_stats.last_match_at = timezone.now()
            winner_stats.save()

            # Update loser stats
            loser_stats.elo_rating = new_loser_elo
            loser_stats.matches_played += 1
            loser_stats.matches_lost += 1
            loser_stats.win_streak = 0  # reset streak on loss
            loser_stats.total_correct += loser.correct_answers
            loser_stats.total_questions += match.total_rounds
            loser_stats.last_match_at = timezone.now()
            loser_stats.save()

            elo_change_total = change

        else:
            # For team / multi-player: update each player's stats
            # Winner gets ELO boost, everyone else loses proportionally
            for participant in participants:
                stats, _ = PlayerArenaStats.objects.get_or_create(
                    player=participant.player,
                    defaults={
                        'elo_rating': 1000,
                        'matches_played': 0,
                        'matches_won': 0,
                        'matches_lost': 0,
                        'win_streak': 0,
                        'best_win_streak': 0,
                        'total_correct': 0,
                        'total_questions': 0,
                    },
                )
                stats.matches_played += 1
                stats.total_correct += participant.correct_answers
                stats.total_questions += match.total_rounds
                stats.last_match_at = timezone.now()

                if participant.id == winner_participant.id:
                    # Winner: gain ELO based on average opponent rating
                    opponent_ratings = [
                        PlayerArenaStats.objects.get_or_create(
                            player=p.player,
                            defaults={'elo_rating': 1000},
                        )[0].elo_rating
                        for p in participants if p.id != participant.id
                    ]
                    avg_opponent = sum(opponent_ratings) / len(opponent_ratings) if opponent_ratings else 1000
                    _, _, change = ArenaService.calculate_elo(
                        stats.elo_rating, int(avg_opponent),
                    )
                    stats.elo_rating += change
                    stats.matches_won += 1
                    stats.win_streak += 1
                    stats.best_win_streak = max(
                        stats.best_win_streak, stats.win_streak
                    )
                    elo_change_total = change
                else:
                    # Loser: lose ELO
                    _, new_rating, _ = ArenaService.calculate_elo(
                        winner_participant.score,  # use winner's rating
                        stats.elo_rating,
                    )
                    stats.elo_rating = max(0, new_rating)
                    stats.matches_lost += 1
                    stats.win_streak = 0

                stats.save()

        match.elo_change = elo_change_total
        match.save(update_fields=['status', 'winner', 'finished_at', 'elo_change'])

        return match
