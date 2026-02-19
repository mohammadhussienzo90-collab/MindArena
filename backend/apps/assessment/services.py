"""Personality assessment scoring and realm mapping."""
from django.utils import timezone


class AssessmentScoringService:
    """Scores personality assessment answers and maps to realm affinities."""

    TRAIT_QUESTIONS = {
        'openness': [0, 5, 10, 15],
        'conscientiousness': [1, 6, 11, 16],
        'extraversion': [2, 7, 12, 17],
        'agreeableness': [3, 8, 13, 18],
        'neuroticism': [4, 9, 14, 19],
        'self_awareness': [20, 25, 30],
        'empathy': [21, 26, 31],
        'emotional_regulation': [22, 27, 32],
        'social_skills': [23, 28, 33],
        'analytical_thinking': [24, 29, 34],
        'creative_thinking': [35, 37, 39],
        'practical_thinking': [36, 38, 40],
        'risk_tolerance': [41, 42, 43, 44],
    }

    REVERSE_SCORED = {4, 9, 14, 19, 22, 27}

    @classmethod
    def score_assessment(cls, answers):
        """Score raw answers (list of 1-5 values) into trait scores (0-100)."""
        traits = {}
        for trait, indices in cls.TRAIT_QUESTIONS.items():
            values = []
            for i in indices:
                if i < len(answers):
                    val = answers[i]
                    if i in cls.REVERSE_SCORED:
                        val = 6 - val
                    values.append(val)
            if values:
                avg = sum(values) / len(values)
                traits[trait] = round((avg - 1) / 4 * 100, 1)
            else:
                traits[trait] = 50.0
        return traits

    @classmethod
    def calculate_realm_scores(cls, traits):
        """Map personality traits to realm affinity scores."""
        return {
            'logic_fortress': round(
                traits.get('analytical_thinking', 50) * 0.5 +
                traits.get('conscientiousness', 50) * 0.3 +
                traits.get('practical_thinking', 50) * 0.2, 1
            ),
            'emotion_ocean': round(
                traits.get('empathy', 50) * 0.4 +
                traits.get('self_awareness', 50) * 0.3 +
                traits.get('emotional_regulation', 50) * 0.3, 1
            ),
            'creativity_nebula': round(
                traits.get('creative_thinking', 50) * 0.5 +
                traits.get('openness', 50) * 0.3 +
                traits.get('risk_tolerance', 50) * 0.2, 1
            ),
            'discipline_citadel': round(
                traits.get('conscientiousness', 50) * 0.5 +
                traits.get('emotional_regulation', 50) * 0.3 +
                (100 - traits.get('neuroticism', 50)) * 0.2, 1
            ),
            'knowledge_peaks': round(
                traits.get('analytical_thinking', 50) * 0.3 +
                traits.get('openness', 50) * 0.4 +
                traits.get('practical_thinking', 50) * 0.3, 1
            ),
            'social_bridge': round(
                traits.get('social_skills', 50) * 0.4 +
                traits.get('extraversion', 50) * 0.3 +
                traits.get('agreeableness', 50) * 0.3, 1
            ),
            'wealth_garden': round(
                traits.get('practical_thinking', 50) * 0.4 +
                traits.get('risk_tolerance', 50) * 0.3 +
                traits.get('conscientiousness', 50) * 0.3, 1
            ),
            'wellness_grove': round(
                traits.get('self_awareness', 50) * 0.3 +
                traits.get('emotional_regulation', 50) * 0.3 +
                (100 - traits.get('neuroticism', 50)) * 0.2 +
                traits.get('conscientiousness', 50) * 0.2, 1
            ),
        }

    @classmethod
    def process_assessment(cls, player, answers):
        """Full pipeline: score answers, update assessment, map realms."""
        from .models import PersonalityAssessment

        traits = cls.score_assessment(answers)
        realm_scores = cls.calculate_realm_scores(traits)

        assessment, _ = PersonalityAssessment.objects.update_or_create(
            player=player,
            defaults={
                **{k: v for k, v in traits.items() if k != 'learning_style'},
                'raw_answers': {'answers': answers, 'version': 1},
                'completed_at': timezone.now(),
            }
        )

        # Initialize realm stats based on assessment
        from apps.progression.models import PlayerRealmStat
        from apps.realms.models import Realm

        for realm_slug, score in realm_scores.items():
            try:
                realm = Realm.objects.get(slug=realm_slug)
                stat, created = PlayerRealmStat.objects.get_or_create(
                    player=player, realm=realm,
                )
                if created:
                    initial_xp = int(score * 2)
                    stat.realm_xp = initial_xp
                    stat.save()
            except Realm.DoesNotExist:
                pass

        player.onboarding_done = True
        player.save(update_fields=['onboarding_done'])

        return {
            'traits': traits,
            'realm_scores': realm_scores,
        }
