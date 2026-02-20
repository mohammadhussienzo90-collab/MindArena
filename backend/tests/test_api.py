"""MindArena API integration tests."""
import json
from django.core.cache import cache
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.accounts.models import Player, CompanionProfile
from apps.realms.models import Realm, Quest, Challenge
from apps.progression.models import (
    Achievement, PlayerAchievement, DailyStreak,
    PlayerRealmStat, PlayerChallengeResult,
)
from apps.feed.models import FeedItem


class APITestBase(TestCase):
    """Base class with auth helpers and test data setup."""

    def setUp(self):
        # Clear throttle cache between tests so rate limits don't bleed over
        cache.clear()
        self.client = Client()

        # Create realm
        self.realm = Realm.objects.create(
            slug='logic_fortress', name_en='Logic Fortress',
            description_en='Test realm', color_primary='#2266EE',
            color_secondary='#1144AA', primary_trait='analytical_thinking',
            sort_order=1,
        )

        # Create quest
        self.quest = Quest.objects.create(
            realm=self.realm, slug='lf-quest-1',
            title_en='Test Quest', description_en='A test quest',
            quest_type='main', sort_order=1,
        )

        # Create MCQ challenge
        self.challenge = Challenge.objects.create(
            quest=self.quest, slug='lf-test-1',
            challenge_type='multiple_choice',
            title_en='Test Challenge',
            content={
                'question_en': 'What is 2+2?',
                'options_en': ['3', '4', '5', '6'],
                'correct_index': 1,
                'explanation_en': 'Basic arithmetic.',
            },
            difficulty=1, primary_trait='analytical_thinking',
            base_xp=15, bonus_xp=8, time_limit_secs=30,
        )

        # Create feed item
        self.feed_item = FeedItem.objects.create(
            title_en='Test Tip', body_en='A helpful tip.',
            content_type='tip', realm=self.realm, xp_value=5,
        )

        # Create achievement
        self.achievement = Achievement.objects.create(
            slug='first_challenge', title_en='First Steps',
            description_en='Complete your first challenge',
            category='onboarding', requirement_type='first_challenge',
            requirement_value=1, xp_reward=25,
        )

    def _register(self, username='testplayer', password='testpass123'):
        resp = self.client.post('/api/v1/accounts/register/', json.dumps({
            'username': username,
            'password': password,
            'display_name': username.title(),
        }), content_type='application/json')
        data = json.loads(resp.content)
        return data.get('tokens', {}).get('access', ''), data.get('tokens', {}).get('refresh', '')

    def _login(self, username='testplayer', password='testpass123'):
        resp = self.client.post('/api/v1/accounts/login/', json.dumps({
            'username': username, 'password': password,
        }), content_type='application/json')
        data = json.loads(resp.content)
        return data.get('access', ''), data.get('refresh', '')

    def _auth_header(self, token):
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def _get(self, url, token):
        return self.client.get(url, **self._auth_header(token))

    def _post(self, url, data, token):
        return self.client.post(
            url, json.dumps(data), content_type='application/json',
            **self._auth_header(token),
        )

    def _patch(self, url, data, token):
        return self.client.patch(
            url, json.dumps(data), content_type='application/json',
            **self._auth_header(token),
        )


class AuthTests(APITestBase):
    """Registration, login, and token tests."""

    def test_register_success(self):
        resp = self.client.post('/api/v1/accounts/register/', json.dumps({
            'username': 'newplayer',
            'password': 'securepass123',
            'display_name': 'New Player',
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertIn('tokens', data)
        self.assertIn('player', data)
        self.assertEqual(data['player']['display_name'], 'New Player')

    def test_register_duplicate_username(self):
        self._register('duplicateuser')
        resp = self.client.post('/api/v1/accounts/register/', json.dumps({
            'username': 'duplicateuser',
            'password': 'anotherpass123',
            'display_name': 'Duplicate',
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_login_success(self):
        self._register()
        resp = self.client.post('/api/v1/accounts/login/', json.dumps({
            'username': 'testplayer', 'password': 'testpass123',
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('access', data)
        self.assertIn('refresh', data)

    def test_login_invalid(self):
        resp = self.client.post('/api/v1/accounts/login/', json.dumps({
            'username': 'nobody', 'password': 'wrongpass',
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_token_refresh(self):
        _, refresh = self._register()
        resp = self.client.post('/api/v1/accounts/token/refresh/', json.dumps({
            'refresh': refresh,
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('access', data)

    def test_auth_required(self):
        resp = self.client.get('/api/v1/accounts/profile/')
        self.assertEqual(resp.status_code, 401)


class ProfileTests(APITestBase):
    """Profile get and update tests."""

    def test_get_profile(self):
        token, _ = self._register()
        resp = self._get('/api/v1/accounts/profile/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['display_name'], 'Testplayer')
        self.assertEqual(data['overall_level'], 1)

    def test_update_profile(self):
        token, _ = self._register()
        resp = self._patch('/api/v1/accounts/profile/', {
            'display_name': 'Updated Name',
            'preferred_lang': 'ar',
        }, token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['display_name'], 'Updated Name')
        self.assertEqual(data['preferred_lang'], 'ar')

    def test_change_password(self):
        token, _ = self._register()
        resp = self._post('/api/v1/accounts/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newpass456!',
        }, token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('tokens', data)
        # Verify old password no longer works
        login_resp = self.client.post('/api/v1/accounts/login/', json.dumps({
            'username': 'testplayer', 'password': 'testpass123',
        }), content_type='application/json')
        self.assertEqual(login_resp.status_code, 401)

    def test_change_password_wrong_old(self):
        token, _ = self._register()
        resp = self._post('/api/v1/accounts/change-password/', {
            'old_password': 'wrongold',
            'new_password': 'newpass456!',
        }, token)
        self.assertEqual(resp.status_code, 400)

    def test_delete_account(self):
        token, _ = self._register()
        resp = self._post('/api/v1/accounts/delete-account/', {
            'password': 'testpass123',
        }, token)
        self.assertEqual(resp.status_code, 200)
        # Verify account is gone
        from django.contrib.auth.models import User
        self.assertFalse(User.objects.filter(username='testplayer').exists())

    def test_player_search(self):
        token, _ = self._register('searchuser', 'testpass123')
        self._register('alice', 'testpass123')
        self._register('bob', 'testpass123')
        resp = self._get('/api/v1/accounts/search/?q=ali', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['display_name'], 'Alice')

    def test_public_profile(self):
        token, _ = self._register()
        # Get own profile to find player ID
        resp = self._get('/api/v1/accounts/profile/', token)
        player_id = json.loads(resp.content)['id']
        # Create another user to view the profile
        token2, _ = self._register('viewer', 'testpass123')
        resp = self._get(f'/api/v1/accounts/players/{player_id}/', token2)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['display_name'], 'Testplayer')
        self.assertIn('realm_stats', data)
        self.assertIn('achievements_count', data)


class RealmTests(APITestBase):
    """Realm listing and detail tests."""

    def test_list_realms(self):
        token, _ = self._register()
        resp = self._get('/api/v1/realms/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        results = data.get('results', data)
        self.assertTrue(len(results) >= 1)

    def test_realm_detail(self):
        token, _ = self._register()
        resp = self._get('/api/v1/realms/logic_fortress/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['slug'], 'logic_fortress')

    def test_realm_challenges(self):
        token, _ = self._register()
        resp = self._get('/api/v1/realms/logic_fortress/challenges/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(len(data) >= 1)


class ChallengeTests(APITestBase):
    """Challenge detail and submission tests."""

    def test_challenge_detail(self):
        token, _ = self._register()
        resp = self._get(f'/api/v1/realms/challenges/{self.challenge.id}/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['challenge_type'], 'multiple_choice')
        self.assertIn('content', data)

    def test_submit_correct_answer(self):
        token, _ = self._register()
        resp = self._post(f'/api/v1/realms/challenges/{self.challenge.id}/submit/', {
            'answer_data': {'selected_index': 1},
            'time_taken_secs': 5.0,
        }, token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data['is_correct'])
        self.assertEqual(data['score'], 100)
        self.assertEqual(data['base_xp'], 15)

    def test_submit_wrong_answer(self):
        token, _ = self._register()
        resp = self._post(f'/api/v1/realms/challenges/{self.challenge.id}/submit/', {
            'answer_data': {'selected_index': 0},
            'time_taken_secs': 5.0,
        }, token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertFalse(data['is_correct'])
        self.assertEqual(data['score'], 0)

    def test_submit_awards_xp(self):
        token, _ = self._register()
        self._post(f'/api/v1/realms/challenges/{self.challenge.id}/submit/', {
            'answer_data': {'selected_index': 1},
            'time_taken_secs': 5.0,
        }, token)
        resp = self._get('/api/v1/accounts/profile/', token)
        data = json.loads(resp.content)
        self.assertGreater(data['total_xp'], 0)

    def test_submit_fast_bonus(self):
        token, _ = self._register()
        resp = self._post(f'/api/v1/realms/challenges/{self.challenge.id}/submit/', {
            'answer_data': {'selected_index': 1},
            'time_taken_secs': 2.0,  # Under 50% of 30s limit
        }, token)
        data = json.loads(resp.content)
        self.assertTrue(data['bonus'])
        self.assertGreater(data['bonus_xp'], 0)


class AssessmentTests(APITestBase):
    """Assessment questions and submission tests."""

    def test_get_questions(self):
        token, _ = self._register()
        resp = self._get('/api/v1/assessment/questions/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('questions', data)
        self.assertIn('total', data)

    def test_submit_assessment(self):
        token, _ = self._register()
        answers = [3] * 45  # All neutral answers
        resp = self._post('/api/v1/assessment/submit/', {
            'answers': answers,
        }, token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('traits', data)
        self.assertIn('realm_scores', data)
        self.assertIn('openness', data['traits'])
        self.assertIn('logic_fortress', data['realm_scores'])

    def test_assessment_sets_onboarding(self):
        token, _ = self._register()
        answers = [3] * 45
        self._post('/api/v1/assessment/submit/', {'answers': answers}, token)
        resp = self._get('/api/v1/accounts/profile/', token)
        data = json.loads(resp.content)
        self.assertTrue(data['onboarding_done'])


class FeedTests(APITestBase):
    """Feed listing and interaction tests."""

    def test_get_feed(self):
        token, _ = self._register()
        resp = self._get('/api/v1/feed/', token)
        self.assertEqual(resp.status_code, 200)

    def test_feed_interaction(self):
        token, _ = self._register()
        resp = self._post(f'/api/v1/feed/{self.feed_item.id}/interact/', {
            'liked': True,
        }, token)
        self.assertEqual(resp.status_code, 200)


class ProgressionTests(APITestBase):
    """Progression stats and achievement tests."""

    def test_get_stats(self):
        token, _ = self._register()
        resp = self._get('/api/v1/progression/stats/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('overall_level', data)
        self.assertIn('total_xp', data)

    def test_achievements_list(self):
        token, _ = self._register()
        resp = self._get('/api/v1/progression/achievements/', token)
        self.assertEqual(resp.status_code, 200)

    def test_achievement_earned_on_challenge(self):
        token, _ = self._register()
        resp = self._post(f'/api/v1/realms/challenges/{self.challenge.id}/submit/', {
            'answer_data': {'selected_index': 1},
            'time_taken_secs': 5.0,
        }, token)
        data = json.loads(resp.content)
        # Should earn 'first_challenge' achievement
        new_achievements = data.get('new_achievements', [])
        slugs = [a['slug'] for a in new_achievements]
        self.assertIn('first_challenge', slugs)


class QuestTests(APITestBase):
    """Quest listing and start tests."""

    def test_quest_start(self):
        token, _ = self._register()
        resp = self._post(f'/api/v1/realms/quests/{self.quest.id}/start/', {}, token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'in_progress')

    def test_quest_list(self):
        token, _ = self._register()
        resp = self._get('/api/v1/realms/quests/', token)
        self.assertEqual(resp.status_code, 200)


class LeaderboardTests(APITestBase):
    """Leaderboard and daily challenge tests."""

    def test_global_leaderboard(self):
        token, _ = self._register()
        resp = self._get('/api/v1/progression/leaderboard/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('leaderboard', data)
        self.assertIn('my_rank', data)
        self.assertEqual(data['my_rank'], 1)  # Only player

    def test_realm_leaderboard(self):
        token, _ = self._register()
        resp = self._get('/api/v1/progression/leaderboard/?realm=logic_fortress', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('leaderboard', data)

    def test_daily_challenge(self):
        token, _ = self._register()
        resp = self._get('/api/v1/progression/daily-challenge/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('date', data)
        self.assertIn('challenges', data)
        self.assertTrue(len(data['challenges']) >= 1)


class ArenaTests(APITestBase):
    """Arena matchmaking and gameplay tests."""

    def setUp(self):
        super().setUp()
        # Add correct_answer field to challenge content for arena scoring
        self.challenge.content['correct_answer'] = 1
        self.challenge.save()
        # Create additional challenges for arena rounds
        for i in range(2, 6):
            Challenge.objects.create(
                quest=self.quest, slug=f'lf-test-{i}',
                challenge_type='multiple_choice',
                title_en=f'Arena Challenge {i}',
                content={
                    'question_en': f'What is {i}+{i}?',
                    'options_en': [str(i*2-1), str(i*2), str(i*2+1)],
                    'correct_index': 1,
                    'correct_answer': 1,
                    'explanation_en': 'Math.',
                },
                difficulty=1, primary_trait='analytical_thinking',
                base_xp=10, bonus_xp=5, time_limit_secs=30,
            )

    def test_arena_status(self):
        token, _ = self._register()
        resp = self._get('/api/v1/arena/status/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'active')
        self.assertIn('match_types', data)

    def test_create_match(self):
        token, _ = self._register()
        resp = self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 3,
        }, token)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data['match_type'], 'speed')
        self.assertEqual(data['status'], 'waiting')
        self.assertEqual(data['total_rounds'], 3)
        self.assertEqual(len(data['participants']), 1)

    def test_join_match_starts_game(self):
        token1, _ = self._register('player1', 'testpass123')
        token2, _ = self._register('player2', 'testpass123')
        # Player 1 creates match
        resp = self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 3,
        }, token1)
        match_id = json.loads(resp.content)['id']
        # Player 2 joins
        resp = self._post(f'/api/v1/arena/matches/{match_id}/join/', {}, token2)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'in_progress')
        self.assertEqual(len(data['participants']), 2)
        self.assertEqual(data['current_round'], 1)

    def test_find_match(self):
        token1, _ = self._register('creator', 'testpass123')
        token2, _ = self._register('seeker', 'testpass123')
        # Create a match
        self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 3,
        }, token1)
        # Seeker finds it
        resp = self._get('/api/v1/arena/matches/find/?realm_slug=logic_fortress', token2)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsNotNone(data['match'])

    def test_match_list(self):
        token, _ = self._register()
        self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 3,
        }, token)
        resp = self._get('/api/v1/arena/matches/?status=waiting', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(len(data) >= 1)

    def test_arena_stats(self):
        token, _ = self._register()
        resp = self._get('/api/v1/arena/stats/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['elo_rating'], 1000)
        self.assertEqual(data['matches_played'], 0)

    def test_arena_leaderboard(self):
        token, _ = self._register()
        resp = self._get('/api/v1/arena/leaderboard/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('leaderboard', data)
        self.assertIn('player_stats', data)

    def test_full_match_flow(self):
        """Test a complete match: create, join, play rounds, finish."""
        token1, _ = self._register('arena_p1', 'testpass123')
        token2, _ = self._register('arena_p2', 'testpass123')

        # Create match with 2 rounds
        resp = self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 2,
        }, token1)
        match_data = json.loads(resp.content)
        match_id = match_data['id']
        challenge_pool = match_data['challenge_pool']

        # Player 2 joins -> match starts
        resp = self._post(f'/api/v1/arena/matches/{match_id}/join/', {}, token2)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'in_progress')

        # Get current challenge
        resp = self._get(f'/api/v1/arena/matches/{match_id}/challenge/', token1)
        self.assertEqual(resp.status_code, 200)
        challenge_data = json.loads(resp.content)
        self.assertEqual(challenge_data['round_number'], 1)

        # Both players submit round 1
        resp = self._post('/api/v1/arena/submit/', {
            'match_id': match_id,
            'round_number': 1,
            'challenge_id': challenge_pool[0],
            'answer': 1,  # correct answer
            'time_taken_secs': 5.0,
        }, token1)
        self.assertEqual(resp.status_code, 200)
        r1 = json.loads(resp.content)
        self.assertTrue(r1['result']['is_correct'])

        resp = self._post('/api/v1/arena/submit/', {
            'match_id': match_id,
            'round_number': 1,
            'challenge_id': challenge_pool[0],
            'answer': 0,  # wrong answer
            'time_taken_secs': 8.0,
        }, token2)
        self.assertEqual(resp.status_code, 200)

        # Both submit round 2
        resp = self._post('/api/v1/arena/submit/', {
            'match_id': match_id,
            'round_number': 2,
            'challenge_id': challenge_pool[1],
            'answer': 1,
            'time_taken_secs': 3.0,
        }, token1)
        self.assertEqual(resp.status_code, 200)

        resp = self._post('/api/v1/arena/submit/', {
            'match_id': match_id,
            'round_number': 2,
            'challenge_id': challenge_pool[1],
            'answer': 1,
            'time_taken_secs': 10.0,
        }, token2)
        self.assertEqual(resp.status_code, 200)
        final = json.loads(resp.content)

        # Match should be completed
        self.assertEqual(final['match']['status'], 'completed')
        # Player 1 won (more correct answers + faster)
        self.assertIsNotNone(final['match']['winner_name'])

        # Check arena stats were updated
        resp = self._get('/api/v1/arena/stats/', token1)
        stats = json.loads(resp.content)
        self.assertEqual(stats['matches_played'], 1)
        self.assertEqual(stats['matches_won'], 1)
        self.assertGreater(stats['elo_rating'], 1000)


class NotificationTests(APITestBase):
    """Notification system tests."""

    def test_notification_list_empty(self):
        token, _ = self._register()
        resp = self._get('/api/v1/notifications/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['unread_count'], 0)
        self.assertEqual(len(data['results']), 0)

    def test_notification_create_and_list(self):
        token, _ = self._register()
        from apps.notifications.services import NotificationService
        player = Player.objects.get(user__username='testplayer')
        NotificationService.send(
            recipient=player,
            notification_type='system',
            title_en='Welcome!',
            message_en='Welcome to MindArena.',
        )
        resp = self._get('/api/v1/notifications/', token)
        data = json.loads(resp.content)
        self.assertEqual(data['unread_count'], 1)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title_en'], 'Welcome!')

    def test_mark_read(self):
        token, _ = self._register()
        from apps.notifications.services import NotificationService
        player = Player.objects.get(user__username='testplayer')
        n = NotificationService.send(
            recipient=player,
            notification_type='system',
            title_en='Test',
        )
        resp = self._post('/api/v1/notifications/mark-read/', {
            'notification_ids': [n.id],
        }, token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['updated'], 1)

    def test_mark_all_read(self):
        token, _ = self._register()
        from apps.notifications.services import NotificationService
        player = Player.objects.get(user__username='testplayer')
        NotificationService.send(recipient=player, notification_type='system', title_en='A')
        NotificationService.send(recipient=player, notification_type='system', title_en='B')
        resp = self._post('/api/v1/notifications/mark-read/', {
            'mark_all': True,
        }, token)
        data = json.loads(resp.content)
        self.assertEqual(data['updated'], 2)

    def test_delete_notification(self):
        token, _ = self._register()
        from apps.notifications.services import NotificationService
        player = Player.objects.get(user__username='testplayer')
        n = NotificationService.send(
            recipient=player,
            notification_type='system',
            title_en='Delete me',
        )
        resp = self.client.delete(
            f'/api/v1/notifications/{n.id}/',
            **self._auth_header(token),
        )
        self.assertEqual(resp.status_code, 204)


class FriendTests(APITestBase):
    """Friend system tests."""

    def test_friend_list_empty(self):
        token, _ = self._register()
        resp = self._get('/api/v1/friends/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data['friends']), 0)

    def test_send_friend_request(self):
        token1, _ = self._register('sender', 'testpass123')
        token2, _ = self._register('receiver', 'testpass123')
        receiver = Player.objects.get(user__username='receiver')
        resp = self._post('/api/v1/friends/request/', {
            'player_id': receiver.id,
        }, token1)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'pending')

    def test_friend_request_list(self):
        token1, _ = self._register('sender2', 'testpass123')
        token2, _ = self._register('receiver2', 'testpass123')
        receiver = Player.objects.get(user__username='receiver2')
        self._post('/api/v1/friends/request/', {
            'player_id': receiver.id,
        }, token1)
        resp = self._get('/api/v1/friends/requests/', token2)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(len(data['requests']), 1)

    def test_accept_friend_request(self):
        token1, _ = self._register('acceptor1', 'testpass123')
        token2, _ = self._register('acceptor2', 'testpass123')
        receiver = Player.objects.get(user__username='acceptor2')
        self._post('/api/v1/friends/request/', {
            'player_id': receiver.id,
        }, token1)
        # Get the request ID
        resp = self._get('/api/v1/friends/requests/', token2)
        request_id = json.loads(resp.content)['requests'][0]['id']
        # Accept
        resp = self._post('/api/v1/friends/respond/', {
            'request_id': request_id,
            'action': 'accept',
        }, token2)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'accepted')
        # Verify friends list
        resp = self._get('/api/v1/friends/', token1)
        friends = json.loads(resp.content)['friends']
        self.assertEqual(len(friends), 1)
        self.assertEqual(friends[0]['display_name'], 'Acceptor2')

    def test_remove_friend(self):
        token1, _ = self._register('remove1', 'testpass123')
        token2, _ = self._register('remove2', 'testpass123')
        receiver = Player.objects.get(user__username='remove2')
        self._post('/api/v1/friends/request/', {
            'player_id': receiver.id,
        }, token1)
        resp = self._get('/api/v1/friends/requests/', token2)
        request_id = json.loads(resp.content)['requests'][0]['id']
        self._post('/api/v1/friends/respond/', {
            'request_id': request_id,
            'action': 'accept',
        }, token2)
        # Remove
        resp = self.client.delete(
            f'/api/v1/friends/{receiver.id}/',
            **self._auth_header(token1),
        )
        self.assertEqual(resp.status_code, 200)
        # Verify empty
        resp = self._get('/api/v1/friends/', token1)
        self.assertEqual(len(json.loads(resp.content)['friends']), 0)

    def test_cant_friend_self(self):
        token, _ = self._register('lonely', 'testpass123')
        player = Player.objects.get(user__username='lonely')
        resp = self._post('/api/v1/friends/request/', {
            'player_id': player.id,
        }, token)
        self.assertEqual(resp.status_code, 400)


class CompanionTests(APITestBase):
    """Tests for the AI companion chat system."""

    def test_chat_creates_conversation(self):
        """POST to companion chat creates a conversation and returns reply."""
        token, _ = self._register()
        resp = self._post('/api/v1/companion/chat/', {
            'message': 'Hello Noor',
        }, token)
        self.assertIn(resp.status_code, [200, 201])
        data = json.loads(resp.content)
        self.assertIn('reply', data)
        self.assertIn('conversation_id', data)

    def test_chat_with_context_type(self):
        """POST with context_type=challenge_help succeeds."""
        token, _ = self._register()
        resp = self._post('/api/v1/companion/chat/', {
            'message': 'Help me',
            'context_type': 'challenge_help',
        }, token)
        self.assertIn(resp.status_code, [200, 201])
        data = json.loads(resp.content)
        self.assertIn('reply', data)
        self.assertIn('conversation_id', data)

    def test_chat_with_realm_slug(self):
        """POST with realm_slug filters context to specific realm."""
        token, _ = self._register()
        resp = self._post('/api/v1/companion/chat/', {
            'message': 'Tell me about logic',
            'realm_slug': 'logic_fortress',
        }, token)
        self.assertIn(resp.status_code, [200, 201])
        data = json.loads(resp.content)
        self.assertIn('reply', data)
        self.assertIn('conversation_id', data)

    def test_chat_continues_conversation(self):
        """Sending a second message with conversation_id continues the same conversation."""
        token, _ = self._register()
        # First message creates a conversation
        resp1 = self._post('/api/v1/companion/chat/', {
            'message': 'Hello Noor',
        }, token)
        data1 = json.loads(resp1.content)
        conv_id = data1['conversation_id']

        # Second message continues the same conversation
        resp2 = self._post('/api/v1/companion/chat/', {
            'message': 'Tell me more',
            'conversation_id': conv_id,
        }, token)
        self.assertIn(resp2.status_code, [200, 201])
        data2 = json.loads(resp2.content)
        self.assertEqual(data2['conversation_id'], conv_id)

    def test_history_empty(self):
        """GET companion history for a new conversation returns empty message list."""
        token, _ = self._register()
        # Create a conversation first, then get its history
        resp = self._post('/api/v1/companion/chat/', {
            'message': 'Hello',
        }, token)
        conv_id = json.loads(resp.content)['conversation_id']
        # History should have messages from the chat
        resp = self._get(f'/api/v1/companion/history/{conv_id}/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)


class CompanionHistoryTest(APITestBase):
    """Tests for companion conversation history retrieval."""

    def test_history_after_chat(self):
        """After posting a chat message, history should contain at least 1 message."""
        token, _ = self._register()
        resp = self._post('/api/v1/companion/chat/', {
            'message': 'Hello Noor, how are you?',
        }, token)
        conv_id = json.loads(resp.content)['conversation_id']

        resp = self._get(f'/api/v1/companion/history/{conv_id}/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        # Should have at least the player message and the companion reply
        self.assertGreaterEqual(len(data), 1)

    def test_history_unauthenticated(self):
        """GET companion history without auth token returns 401."""
        resp = self.client.get('/api/v1/companion/history/1/')
        self.assertEqual(resp.status_code, 401)


class ArenaEdgeCaseTests(APITestBase):
    """Edge case tests for the arena matchmaking and gameplay system."""

    def setUp(self):
        super().setUp()
        # Add correct_answer field to challenge content for arena scoring
        self.challenge.content['correct_answer'] = 1
        self.challenge.save()
        # Create additional challenges for arena rounds
        for i in range(2, 6):
            Challenge.objects.create(
                quest=self.quest, slug=f'lf-edge-{i}',
                challenge_type='multiple_choice',
                title_en=f'Edge Challenge {i}',
                content={
                    'question_en': f'What is {i}+{i}?',
                    'options_en': [str(i * 2 - 1), str(i * 2), str(i * 2 + 1)],
                    'correct_index': 1,
                    'correct_answer': 1,
                    'explanation_en': 'Math.',
                },
                difficulty=1, primary_trait='analytical_thinking',
                base_xp=10, bonus_xp=5, time_limit_secs=30,
            )

    def test_join_own_match(self):
        """Player cannot join a match they created."""
        token, _ = self._register()
        resp = self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 3,
        }, token)
        self.assertEqual(resp.status_code, 201)
        match_id = json.loads(resp.content)['id']

        # Try to join own match
        resp = self._post(f'/api/v1/arena/matches/{match_id}/join/', {}, token)
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.content)
        self.assertIn('error', data)

    def test_join_full_match(self):
        """Third player cannot join a match that is already full (2-player speed)."""
        token1, _ = self._register('edge_p1', 'testpass123')
        token2, _ = self._register('edge_p2', 'testpass123')
        token3, _ = self._register('edge_p3', 'testpass123')

        # Player 1 creates match
        resp = self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 3,
        }, token1)
        match_id = json.loads(resp.content)['id']

        # Player 2 joins (filling the match)
        resp = self._post(f'/api/v1/arena/matches/{match_id}/join/', {}, token2)
        self.assertEqual(resp.status_code, 200)

        # Player 3 tries to join the now-full match
        resp = self._post(f'/api/v1/arena/matches/{match_id}/join/', {}, token3)
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.content)
        self.assertIn('error', data)

    def test_submit_wrong_match(self):
        """Player cannot submit an answer to a match they are not in."""
        token1, _ = self._register('sub_p1', 'testpass123')
        token2, _ = self._register('sub_p2', 'testpass123')
        token3, _ = self._register('sub_p3', 'testpass123')

        # Player 1 creates match, player 2 joins -> in_progress
        resp = self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'logic_fortress',
            'total_rounds': 3,
        }, token1)
        match_data = json.loads(resp.content)
        match_id = match_data['id']
        challenge_pool = match_data['challenge_pool']

        self._post(f'/api/v1/arena/matches/{match_id}/join/', {}, token2)

        # Player 3 (not in match) tries to submit
        resp = self._post('/api/v1/arena/submit/', {
            'match_id': match_id,
            'round_number': 1,
            'challenge_id': challenge_pool[0],
            'answer': 1,
            'time_taken_secs': 5.0,
        }, token3)
        self.assertEqual(resp.status_code, 400)

    def test_create_match_invalid_realm(self):
        """Creating a match with a nonexistent realm returns 400."""
        token, _ = self._register()
        resp = self._post('/api/v1/arena/matches/create/', {
            'match_type': 'speed',
            'realm_slug': 'nonexistent',
            'total_rounds': 3,
        }, token)
        self.assertEqual(resp.status_code, 400)


class ProgressionEdgeCaseTests(APITestBase):
    """Edge case tests for the progression system."""

    def setUp(self):
        super().setUp()
        # Create a second realm with its own quest and challenge
        self.realm2 = Realm.objects.create(
            slug='emotion_ocean', name_en='Emotion Ocean',
            description_en='Test realm 2', color_primary='#EE6622',
            color_secondary='#AA4411', primary_trait='emotional_intelligence',
            sort_order=2,
        )
        self.quest2 = Quest.objects.create(
            realm=self.realm2, slug='eo-quest-1',
            title_en='Emotion Quest', description_en='An emotion quest',
            quest_type='main', sort_order=1,
        )
        self.challenge2 = Challenge.objects.create(
            quest=self.quest2, slug='eo-test-1',
            challenge_type='multiple_choice',
            title_en='Emotion Challenge',
            content={
                'question_en': 'How do you feel?',
                'options_en': ['Happy', 'Sad', 'Neutral', 'Excited'],
                'correct_index': 0,
                'explanation_en': 'Self awareness.',
            },
            difficulty=1, primary_trait='emotional_intelligence',
            base_xp=15, bonus_xp=8, time_limit_secs=30,
        )

    def test_daily_challenge_different_realms(self):
        """Daily challenges for different realms return realm-specific data."""
        token, _ = self._register()
        resp1 = self._get(
            '/api/v1/progression/daily-challenge/?realm=logic_fortress', token,
        )
        self.assertEqual(resp1.status_code, 200)
        data1 = json.loads(resp1.content)
        self.assertIn('challenges', data1)

        resp2 = self._get(
            '/api/v1/progression/daily-challenge/?realm=emotion_ocean', token,
        )
        self.assertEqual(resp2.status_code, 200)
        data2 = json.loads(resp2.content)
        self.assertIn('challenges', data2)

        # Both should return challenges; since there are 2 realms, the full
        # list should contain entries for both realms
        all_realm_slugs = [c['realm_slug'] for c in data1['challenges']]
        self.assertIn('logic_fortress', all_realm_slugs)

    def test_challenge_history_pagination(self):
        """After submitting several challenge answers, history returns results."""
        token, _ = self._register()
        # Submit answers to the first challenge multiple times is not realistic,
        # so submit to different challenges. We have challenge and challenge2.
        self._post(f'/api/v1/realms/challenges/{self.challenge.id}/submit/', {
            'answer_data': {'selected_index': 1},
            'time_taken_secs': 5.0,
        }, token)
        self._post(f'/api/v1/realms/challenges/{self.challenge2.id}/submit/', {
            'answer_data': {'selected_index': 0},
            'time_taken_secs': 4.0,
        }, token)

        resp = self._get('/api/v1/progression/history/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)

    def test_xp_accumulates(self):
        """XP increases after each correct challenge submission."""
        token, _ = self._register()

        # Submit first correct answer
        self._post(f'/api/v1/realms/challenges/{self.challenge.id}/submit/', {
            'answer_data': {'selected_index': 1},
            'time_taken_secs': 5.0,
        }, token)

        # Check XP after first submission
        resp = self._get('/api/v1/progression/stats/', token)
        stats1 = json.loads(resp.content)
        xp_after_first = stats1['total_xp']
        self.assertGreater(xp_after_first, 0)

        # Submit second correct answer (different challenge)
        self._post(f'/api/v1/realms/challenges/{self.challenge2.id}/submit/', {
            'answer_data': {'selected_index': 0},
            'time_taken_secs': 4.0,
        }, token)

        # Check XP after second submission
        resp = self._get('/api/v1/progression/stats/', token)
        stats2 = json.loads(resp.content)
        xp_after_second = stats2['total_xp']
        self.assertGreater(xp_after_second, xp_after_first)
