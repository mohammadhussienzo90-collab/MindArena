# Generated migration for PromptVariant and PromptOutcomeLog

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai_engine', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromptVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('context_type', models.CharField(db_index=True, help_text='Category: frustration_support, encouragement, greeting, etc.', max_length=50)),
                ('strategy', models.CharField(default='default', help_text='Coaching strategy: socratic, growth_mindset, motivational, supportive, challenging', max_length=50)),
                ('prompt_text', models.TextField(help_text='The prompt template text to inject into system prompt.')),
                ('description', models.CharField(blank=True, help_text='Human-readable description of what this variant does differently.', max_length=200)),
                ('positive_outcomes', models.PositiveIntegerField(default=1, help_text='Number of positive outcomes (Beta prior alpha).')),
                ('negative_outcomes', models.PositiveIntegerField(default=1, help_text='Number of negative outcomes (Beta prior beta).')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-positive_outcomes'],
                'unique_together': {('context_type', 'strategy')},
            },
        ),
        migrations.CreateModel(
            name='PromptOutcomeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('player_id', models.IntegerField()),
                ('was_positive', models.BooleanField()),
                ('context_data', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outcomes', to='ai_engine.promptvariant')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['created_at'], name='ai_engine_promptoutcome_created'),
                ],
            },
        ),
    ]
