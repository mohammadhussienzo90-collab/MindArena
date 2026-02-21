"""
Management command: init_ai_engine
====================================
Initialize IRT parameters (ChallengeParameter) for every Challenge in
the database.

Usage:
    python manage.py init_ai_engine
    python manage.py init_ai_engine --force   # Overwrite existing parameters
    python manage.py init_ai_engine --dry-run  # Preview without writing

This command:
1. Creates a ChallengeParameter for every Challenge that does not have one.
2. Converts the human-readable difficulty (1-10) to the IRT b parameter
   using a linear mapping: difficulty 1 -> b = -2.0, difficulty 10 -> b = +2.0.
3. Sets the guessing_c parameter based on challenge_type:
   - multiple_choice:    0.25 (4-option MCQ baseline)
   - pattern_match:      0.20 (some elimination possible)
   - sequence:           0.10 (harder to guess)
   - spatial_puzzle:     0.05 (very hard to guess)
   - timed_response:     0.10
   - scenario_choice:    0.25 (usually 4 options)
   - math_logic:         0.00 (open-ended)
   - emotional_scenario: 0.20 (limited options)
   - creative_prompt:    0.00 (open-ended)
   - memory_test:        0.10
   - debate_analysis:    0.00 (open-ended)
   - financial_decision: 0.20 (limited options)
   - word_puzzle:        0.10
4. Sets default discrimination (a) to 1.0 for all challenges.
5. Prints a summary of initialized parameters.
"""
from django.core.management.base import BaseCommand

from apps.ai_engine.algorithms.irt import IRTEngine
from apps.ai_engine.models import ChallengeParameter
from apps.realms.models import Challenge


# Guessing parameter defaults by challenge type
GUESSING_DEFAULTS = {
    'multiple_choice': 0.25,
    'pattern_match': 0.20,
    'sequence': 0.10,
    'spatial_puzzle': 0.05,
    'timed_response': 0.10,
    'scenario_choice': 0.25,
    'math_logic': 0.00,
    'emotional_scenario': 0.20,
    'creative_prompt': 0.00,
    'memory_test': 0.10,
    'debate_analysis': 0.00,
    'financial_decision': 0.20,
    'word_puzzle': 0.10,
}

# Default discrimination parameter
DEFAULT_DISCRIMINATION = 1.0


class Command(BaseCommand):
    help = (
        'Initialize ChallengeParameter (IRT item parameters) for every '
        'Challenge. Converts difficulty 1-10 to IRT b parameter and sets '
        'guessing_c based on challenge_type.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing ChallengeParameter records.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING(
            'Initializing AI Engine parameters...'
        ))
        self.stdout.write('')

        challenges = Challenge.objects.all().select_related(
            'quest', 'quest__realm',
        ).order_by('quest__realm__slug', 'difficulty')

        total_challenges = challenges.count()
        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Track stats per challenge type and difficulty
        type_stats = {}
        difficulty_stats = {}

        for challenge in challenges:
            # Compute IRT parameters
            b = IRTEngine.initialize_from_difficulty(challenge.difficulty)
            c = GUESSING_DEFAULTS.get(challenge.challenge_type, 0.10)
            a = DEFAULT_DISCRIMINATION

            # Track stats
            ctype = challenge.challenge_type
            type_stats.setdefault(ctype, {'count': 0, 'avg_b': 0, 'c': c})
            type_stats[ctype]['count'] += 1
            type_stats[ctype]['avg_b'] += b

            diff = challenge.difficulty
            difficulty_stats.setdefault(diff, {'count': 0, 'b': b})
            difficulty_stats[diff]['count'] += 1

            if dry_run:
                realm_slug = (
                    challenge.quest.realm.slug
                    if challenge.quest and challenge.quest.realm
                    else 'N/A'
                )
                self.stdout.write(
                    f'  [DRY RUN] {challenge.slug} '
                    f'(realm={realm_slug}, diff={diff}, type={ctype}) '
                    f'-> a={a:.2f}, b={b:.4f}, c={c:.2f}'
                )
                created_count += 1
                continue

            # Check if parameter already exists
            existing = ChallengeParameter.objects.filter(
                challenge=challenge,
            ).first()

            if existing and not force:
                skipped_count += 1
                continue

            if existing and force:
                existing.discrimination = a
                existing.difficulty_b = b
                existing.guessing_c = c
                existing.save()
                updated_count += 1
            else:
                ChallengeParameter.objects.create(
                    challenge=challenge,
                    discrimination=a,
                    difficulty_b=b,
                    guessing_c=c,
                    total_attempts=0,
                    correct_rate=0.5,
                    avg_time_secs=0.0,
                )
                created_count += 1

        # Print summary
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Summary'))
        self.stdout.write(f'  Total challenges: {total_challenges}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'  Would create: {created_count} parameters (dry run)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  Created: {created_count}'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'  Updated: {updated_count}'
            ))
            self.stdout.write(f'  Skipped (already exists): {skipped_count}')

        # Print type breakdown
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(
            'Guessing parameter by challenge type'
        ))
        self.stdout.write(f'  {"Type":<25} {"Count":>6} {"c (guess)":>10}')
        self.stdout.write(f'  {"-" * 25} {"-" * 6} {"-" * 10}')

        for ctype in sorted(type_stats.keys()):
            stats = type_stats[ctype]
            self.stdout.write(
                f'  {ctype:<25} {stats["count"]:>6} {stats["c"]:>10.2f}'
            )

        # Print difficulty mapping
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(
            'Difficulty to IRT b parameter mapping'
        ))
        self.stdout.write(f'  {"Difficulty":>10} {"Count":>6} {"IRT b":>10}')
        self.stdout.write(f'  {"-" * 10} {"-" * 6} {"-" * 10}')

        for diff in sorted(difficulty_stats.keys()):
            stats = difficulty_stats[diff]
            self.stdout.write(
                f'  {diff:>10} {stats["count"]:>6} {stats["b"]:>+10.4f}'
            )

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                'No changes were made (dry run mode). '
                'Remove --dry-run to apply changes.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                'AI Engine initialization complete!'
            ))
