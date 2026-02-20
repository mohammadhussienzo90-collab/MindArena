# Generated manually — Arena full implementation

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arena', '0001_initial'),
        ('accounts', '0001_initial'),
        ('realms', '0001_initial'),
    ]

    operations = [
        # ── ArenaMatch: add new fields ──────────────────────────────
        migrations.AddField(
            model_name='arenamatch',
            name='status',
            field=models.CharField(
                choices=[
                    ('waiting', 'Waiting'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                ],
                default='waiting',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='max_players',
            field=models.IntegerField(default=2),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='current_round',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='total_rounds',
            field=models.IntegerField(default=5),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='challenge_pool',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='winner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='matches_won_arena',
                to='accounts.player',
            ),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='finished_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='arenamatch',
            name='elo_change',
            field=models.IntegerField(default=0),
        ),

        # ── PlayerArenaStats: add new fields ────────────────────────
        migrations.AddField(
            model_name='playerarenastats',
            name='best_win_streak',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playerarenastats',
            name='matches_lost',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playerarenastats',
            name='total_correct',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playerarenastats',
            name='total_questions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='playerarenastats',
            name='last_match_at',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # ── New model: ArenaMatchParticipant ─────────────────────────
        migrations.CreateModel(
            name='ArenaMatchParticipant',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('score', models.IntegerField(default=0)),
                ('correct_answers', models.IntegerField(default=0)),
                ('total_time_secs', models.FloatField(default=0.0)),
                ('is_ready', models.BooleanField(default=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('match', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='participants',
                    to='arena.arenamatch',
                )),
                ('player', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='arena_participations',
                    to='accounts.player',
                )),
            ],
            options={
                'ordering': ['-score'],
                'unique_together': {('match', 'player')},
            },
        ),

        # ── New model: ArenaRoundResult ──────────────────────────────
        migrations.CreateModel(
            name='ArenaRoundResult',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID',
                )),
                ('round_number', models.IntegerField()),
                ('is_correct', models.BooleanField()),
                ('time_taken_secs', models.FloatField()),
                ('score_earned', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('match', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='round_results',
                    to='arena.arenamatch',
                )),
                ('participant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='round_results',
                    to='arena.arenamatchparticipant',
                )),
                ('challenge', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='realms.challenge',
                )),
            ],
            options={
                'ordering': ['round_number'],
                'unique_together': {('match', 'participant', 'round_number')},
            },
        ),
    ]
