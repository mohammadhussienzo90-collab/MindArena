"""WebSocket consumers for real-time arena matches and matchmaking."""
import json
import logging
import random

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class ArenaConsumer(AsyncJsonWebsocketConsumer):
    """Real-time WebSocket consumer for live arena matches.

    Protocol (client → server):
        {"action": "ready"}                          — Signal player is ready
        {"action": "submit_answer", "answer": 2,
         "time_taken": 12.5}                         — Submit round answer
        {"action": "request_challenge"}              — Request current challenge
        {"action": "spectate"}                       — Join as spectator

    Protocol (server → client):
        {"type": "player_joined", ...}               — A player connected
        {"type": "match_starting", "countdown": 3}   — Match countdown
        {"type": "new_round", "round": 1, ...}       — New round with challenge
        {"type": "answer_result", ...}               — Your answer result
        {"type": "score_update", "scores": [...]}    — Updated scores
        {"type": "opponent_answered"}                 — Opponent submitted
        {"type": "match_ended", ...}                 — Final results
        {"type": "error", "message": "..."}          — Error message
    """

    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.match_group = f'arena_match_{self.match_id}'
        self.user = self.scope.get('user')
        self.is_spectator = False

        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return

        self.player = await self._get_player()
        if not self.player:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.match_group, self.channel_name)
        await self.accept()

        # Notify others
        await self.channel_layer.group_send(self.match_group, {
            'type': 'player.joined',
            'player_id': self.player.id,
            'display_name': self.player.display_name,
        })

        logger.info("Player %s connected to match %s", self.player.id, self.match_id)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.match_group, self.channel_name)
        logger.info("Player disconnected from match %s (code=%s)", self.match_id, close_code)

    async def receive_json(self, content):
        action = content.get('action', '')

        if action == 'ready':
            await self._handle_ready()
        elif action == 'submit_answer':
            await self._handle_submit_answer(content)
        elif action == 'request_challenge':
            await self._send_current_challenge()
        elif action == 'spectate':
            self.is_spectator = True
            await self.send_json({'type': 'spectating', 'match_id': int(self.match_id)})
        else:
            await self.send_json({'type': 'error', 'message': f'Unknown action: {action}'})

    # ---- Action handlers ----

    async def _handle_ready(self):
        """Mark player as ready. When all ready, start countdown."""
        await self._set_player_ready()
        all_ready = await self._check_all_ready()

        if all_ready:
            # Start 3-2-1 countdown
            await self.channel_layer.group_send(self.match_group, {
                'type': 'match.starting',
                'countdown': 3,
            })
            # After countdown would complete (handled client-side), start round 1
            import asyncio
            await asyncio.sleep(3.5)
            await self._start_round(1)

    async def _handle_submit_answer(self, content):
        """Process answer submission and broadcast results."""
        if self.is_spectator:
            await self.send_json({'type': 'error', 'message': 'Spectators cannot submit answers'})
            return

        answer = content.get('answer')
        time_taken = content.get('time_taken', 30.0)

        try:
            result = await self._submit_answer_db(answer, time_taken)
        except ValueError as e:
            await self.send_json({'type': 'error', 'message': str(e)})
            return

        # Send result to this player
        await self.send_json({
            'type': 'answer_result',
            'is_correct': result['is_correct'],
            'correct_answer': result['correct_answer'],
            'score_earned': result['score_earned'],
            'total_score': result['participant_total_score'],
        })

        # Broadcast that this player answered
        await self.channel_layer.group_send(self.match_group, {
            'type': 'opponent.answered',
            'player_id': self.player.id,
            'display_name': self.player.display_name,
        })

        # Broadcast updated scores
        scores = await self._get_all_scores()
        await self.channel_layer.group_send(self.match_group, {
            'type': 'score.update',
            'scores': scores,
        })

        # Check if round is complete
        round_complete = await self._is_round_complete()
        if round_complete:
            match_data = await self._get_match_data()
            current_round = match_data['current_round']
            total_rounds = match_data['total_rounds']

            if current_round >= total_rounds:
                # Match is over
                match_result = await self._finish_match()
                await self.channel_layer.group_send(self.match_group, {
                    'type': 'match.ended',
                    'result': match_result,
                })
            else:
                # Advance to next round
                import asyncio
                await asyncio.sleep(2.0)  # Brief pause between rounds
                await self._advance_round_db()
                new_round = current_round + 1
                await self._start_round(new_round)

    async def _send_current_challenge(self):
        """Send the current round's challenge to the requesting client."""
        challenge = await self._get_current_challenge_data()
        if challenge:
            await self.send_json({
                'type': 'current_challenge',
                'challenge': challenge,
            })
        else:
            await self.send_json({'type': 'error', 'message': 'No active challenge'})

    async def _start_round(self, round_number):
        """Broadcast a new round with the challenge data."""
        challenge = await self._get_challenge_for_round(round_number)
        if challenge:
            await self.channel_layer.group_send(self.match_group, {
                'type': 'new.round',
                'round_number': round_number,
                'challenge': challenge,
            })

    # ---- Channel layer event handlers (group_send targets) ----

    async def player_joined(self, event):
        await self.send_json({
            'type': 'player_joined',
            'player_id': event['player_id'],
            'display_name': event['display_name'],
        })

    async def match_starting(self, event):
        await self.send_json({
            'type': 'match_starting',
            'countdown': event['countdown'],
        })

    async def new_round(self, event):
        await self.send_json({
            'type': 'new_round',
            'round_number': event['round_number'],
            'challenge': event['challenge'],
        })

    async def opponent_answered(self, event):
        # Don't send to the player who answered
        if event.get('player_id') != self.player.id:
            await self.send_json({
                'type': 'opponent_answered',
                'display_name': event['display_name'],
            })

    async def score_update(self, event):
        await self.send_json({
            'type': 'score_update',
            'scores': event['scores'],
        })

    async def match_ended(self, event):
        await self.send_json({
            'type': 'match_ended',
            'result': event['result'],
        })

    # ---- Database helpers (sync_to_async) ----

    @database_sync_to_async
    def _get_player(self):
        try:
            return self.user.player
        except Exception:
            return None

    @database_sync_to_async
    def _set_player_ready(self):
        from apps.arena.models import ArenaMatchParticipant
        ArenaMatchParticipant.objects.filter(
            match_id=self.match_id, player=self.player,
        ).update(is_ready=True)

    @database_sync_to_async
    def _check_all_ready(self):
        from apps.arena.models import ArenaMatch
        match = ArenaMatch.objects.get(id=self.match_id)
        total = match.participants.count()
        ready = match.participants.filter(is_ready=True).count()
        return total >= 2 and ready >= total

    @database_sync_to_async
    def _submit_answer_db(self, answer, time_taken):
        from apps.arena.services import ArenaService
        from apps.arena.models import ArenaMatch
        match = ArenaMatch.objects.get(id=self.match_id)
        challenge_id = match.challenge_pool[match.current_round - 1]
        return ArenaService.submit_answer(
            self.player, int(self.match_id),
            match.current_round, challenge_id, answer, time_taken,
        )

    @database_sync_to_async
    def _is_round_complete(self):
        from apps.arena.models import ArenaMatch, ArenaRoundResult
        match = ArenaMatch.objects.get(id=self.match_id)
        total_participants = match.participants.count()
        submissions = ArenaRoundResult.objects.filter(
            match=match, round_number=match.current_round,
        ).count()
        return submissions >= total_participants

    @database_sync_to_async
    def _get_match_data(self):
        from apps.arena.models import ArenaMatch
        match = ArenaMatch.objects.get(id=self.match_id)
        return {
            'current_round': match.current_round,
            'total_rounds': match.total_rounds,
            'status': match.status,
        }

    @database_sync_to_async
    def _advance_round_db(self):
        from apps.arena.models import ArenaMatch
        match = ArenaMatch.objects.select_for_update().get(id=self.match_id)
        match.current_round += 1
        match.save(update_fields=['current_round'])

    @database_sync_to_async
    def _finish_match(self):
        from apps.arena.models import ArenaMatch
        from apps.arena.services import ArenaService
        match = ArenaMatch.objects.select_for_update().get(id=self.match_id)
        ArenaService._finish_match(match)

        # Build result data
        participants = list(match.participants.select_related('player').order_by('-score'))
        result = {
            'winner_id': match.winner_id,
            'winner_name': match.winner.display_name if match.winner else '',
            'elo_change': match.elo_change,
            'scores': [],
        }
        for p in participants:
            result['scores'].append({
                'player_id': p.player_id,
                'display_name': p.player.display_name,
                'score': p.score,
                'correct_answers': p.correct_answers,
                'total_time': round(p.total_time_secs, 1),
            })
        return result

    @database_sync_to_async
    def _get_all_scores(self):
        from apps.arena.models import ArenaMatch
        match = ArenaMatch.objects.get(id=self.match_id)
        scores = []
        for p in match.participants.select_related('player').order_by('-score'):
            scores.append({
                'player_id': p.player_id,
                'display_name': p.player.display_name,
                'score': p.score,
                'correct_answers': p.correct_answers,
            })
        return scores

    @database_sync_to_async
    def _get_current_challenge_data(self):
        from apps.arena.models import ArenaMatch
        from apps.realms.models import Challenge
        try:
            match = ArenaMatch.objects.get(id=self.match_id)
            if match.current_round < 1:
                return None
            challenge_id = match.challenge_pool[match.current_round - 1]
            challenge = Challenge.objects.get(id=challenge_id)
            return _serialize_challenge(challenge)
        except Exception:
            return None

    @database_sync_to_async
    def _get_challenge_for_round(self, round_number):
        from apps.arena.models import ArenaMatch
        from apps.realms.models import Challenge
        try:
            match = ArenaMatch.objects.get(id=self.match_id)
            idx = round_number - 1
            if idx >= len(match.challenge_pool):
                return None
            challenge_id = match.challenge_pool[idx]
            challenge = Challenge.objects.get(id=challenge_id)
            return _serialize_challenge(challenge)
        except Exception:
            return None


class MatchmakingConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for matchmaking queue.

    Protocol (client → server):
        {"action": "queue", "match_type": "speed", "realm_slug": "logic_fortress"}
        {"action": "cancel"}

    Protocol (server → client):
        {"type": "queued", "position": 1}
        {"type": "match_found", "match_id": 42, "opponent": {...}}
        {"type": "cancelled"}
        {"type": "error", "message": "..."}
    """

    # In-memory matchmaking queue (per-process; for production use Redis)
    _queue = {}  # key: (match_type, realm_slug) → list of (player, channel_name, elo)

    async def connect(self):
        self.user = self.scope.get('user')
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return

        self.player = await self._get_player()
        if not self.player:
            await self.close(code=4001)
            return

        self.queue_key = None
        await self.channel_layer.group_add('matchmaking_global', self.channel_name)
        await self.accept()
        logger.info("Player %s joined matchmaking", self.player.id)

    async def disconnect(self, close_code):
        # Remove from queue
        if self.queue_key and self.queue_key in MatchmakingConsumer._queue:
            MatchmakingConsumer._queue[self.queue_key] = [
                entry for entry in MatchmakingConsumer._queue[self.queue_key]
                if entry[0].id != self.player.id
            ]
        await self.channel_layer.group_discard('matchmaking_global', self.channel_name)

    async def receive_json(self, content):
        action = content.get('action', '')

        if action == 'queue':
            await self._handle_queue(content)
        elif action == 'cancel':
            await self._handle_cancel()
        else:
            await self.send_json({'type': 'error', 'message': f'Unknown action: {action}'})

    async def _handle_queue(self, content):
        match_type = content.get('match_type', 'speed')
        realm_slug = content.get('realm_slug', 'logic_fortress')
        self.queue_key = (match_type, realm_slug)

        elo = await self._get_player_elo()

        if self.queue_key not in MatchmakingConsumer._queue:
            MatchmakingConsumer._queue[self.queue_key] = []

        # Add to queue
        queue = MatchmakingConsumer._queue[self.queue_key]
        queue.append((self.player, self.channel_name, elo))

        await self.send_json({
            'type': 'queued',
            'position': len(queue),
            'match_type': match_type,
            'realm_slug': realm_slug,
        })

        # Try to find a match (ELO within 200 range, expanding over time)
        opponent_entry = None
        for entry in queue:
            if entry[0].id != self.player.id and abs(entry[2] - elo) <= 300:
                opponent_entry = entry
                break

        if opponent_entry:
            # Match found! Remove both from queue
            queue.remove(opponent_entry)
            queue.remove((self.player, self.channel_name, elo))

            # Create match in database
            match = await self._create_match(
                self.player, opponent_entry[0], match_type, realm_slug,
            )

            # Notify both players
            match_data = {
                'type': 'match_found',
                'match_id': match.id,
            }

            await self.send_json({
                **match_data,
                'opponent': {
                    'display_name': opponent_entry[0].display_name,
                    'elo': opponent_entry[2],
                },
            })

            # Notify opponent via their channel
            await self.channel_layer.send(opponent_entry[1], {
                'type': 'match.found',
                'match_id': match.id,
                'opponent': {
                    'display_name': self.player.display_name,
                    'elo': elo,
                },
            })

    async def _handle_cancel(self):
        if self.queue_key and self.queue_key in MatchmakingConsumer._queue:
            MatchmakingConsumer._queue[self.queue_key] = [
                entry for entry in MatchmakingConsumer._queue[self.queue_key]
                if entry[0].id != self.player.id
            ]
        self.queue_key = None
        await self.send_json({'type': 'cancelled'})

    async def match_found(self, event):
        """Called when this player's match was found by the opponent's handler."""
        await self.send_json({
            'type': 'match_found',
            'match_id': event['match_id'],
            'opponent': event['opponent'],
        })

    @database_sync_to_async
    def _get_player(self):
        try:
            return self.user.player
        except Exception:
            return None

    @database_sync_to_async
    def _get_player_elo(self):
        from apps.arena.models import PlayerArenaStats
        stats, _ = PlayerArenaStats.objects.get_or_create(
            player=self.player,
            defaults={'elo_rating': 1000},
        )
        return stats.elo_rating

    @database_sync_to_async
    def _create_match(self, player1, player2, match_type, realm_slug):
        from apps.arena.services import ArenaService
        match = ArenaService.create_match(player1, match_type, realm_slug, total_rounds=5)
        ArenaService.join_match(player2, match.id)
        return match


def _serialize_challenge(challenge):
    """Serialize a Challenge model for WebSocket transmission."""
    return {
        'id': challenge.id,
        'challenge_type': challenge.challenge_type,
        'title_en': challenge.title_en,
        'title_ar': getattr(challenge, 'title_ar', ''),
        'difficulty': challenge.difficulty,
        'time_limit_secs': challenge.time_limit_secs or 30,
        'content': {
            'question_en': challenge.content.get('question_en', ''),
            'question_ar': challenge.content.get('question_ar', ''),
            'options_en': challenge.content.get('options_en', []),
            'options_ar': challenge.content.get('options_ar', []),
            # Note: correct_index is NOT sent to prevent cheating
        },
        'base_xp': challenge.base_xp,
    }
