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
    """Arena status test."""

    def test_arena_coming_soon(self):
        token, _ = self._register()
        resp = self._get('/api/v1/arena/status/', token)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['status'], 'coming_soon')
