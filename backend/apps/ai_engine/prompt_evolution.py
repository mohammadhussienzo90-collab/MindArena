"""
Prompt Evolution System
========================
A/B tests coaching strategies and evolves prompts based on player outcomes.
Uses Thompson Sampling (already implemented in the recommender) to select
between prompt variants and tracks which strategies produce the best results.

Usage:
    from apps.ai_engine.prompt_evolution import PromptEvolution
    variant = PromptEvolution.select_variant('frustration_support')
    # ... use variant.prompt_text in response generation ...
    PromptEvolution.record_outcome(variant.id, was_positive=True)
"""
import logging
import random

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class PromptVariant(models.Model):
    """A variant of a coaching prompt that can be A/B tested.

    Each variant tracks its success rate using a Beta distribution
    (positive_outcomes, negative_outcomes) for Thompson Sampling.
    """
    context_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Category: frustration_support, encouragement, greeting, etc.",
    )
    strategy = models.CharField(
        max_length=50,
        default='default',
        help_text="Coaching strategy: socratic, growth_mindset, motivational, supportive, challenging",
    )
    prompt_text = models.TextField(
        help_text="The prompt template text to inject into system prompt.",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human-readable description of what this variant does differently.",
    )
    positive_outcomes = models.PositiveIntegerField(
        default=1,
        help_text="Number of positive outcomes (Beta prior alpha).",
    )
    negative_outcomes = models.PositiveIntegerField(
        default=1,
        help_text="Number of negative outcomes (Beta prior beta).",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'ai_engine'
        unique_together = [('context_type', 'strategy')]
        ordering = ['-positive_outcomes']

    def __str__(self):
        total = self.positive_outcomes + self.negative_outcomes
        rate = self.positive_outcomes / total if total > 0 else 0
        return f"PromptVariant({self.context_type}/{self.strategy} win={rate:.0%})"

    @property
    def success_rate(self):
        total = self.positive_outcomes + self.negative_outcomes
        return self.positive_outcomes / total if total > 0 else 0.5


class PromptOutcomeLog(models.Model):
    """Log of each prompt variant usage and its outcome."""
    variant = models.ForeignKey(
        PromptVariant, on_delete=models.CASCADE, related_name='outcomes',
    )
    player_id = models.IntegerField()
    was_positive = models.BooleanField()
    context_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'ai_engine'
        indexes = [
            models.Index(fields=['created_at']),
        ]


class PromptEvolution:
    """A/B testing engine for coaching prompt strategies."""

    @classmethod
    def select_variant(cls, context_type, player=None):
        """Select the best prompt variant using Thompson Sampling.

        Parameters
        ----------
        context_type : str
            The type of prompt context (e.g., 'frustration_support').
        player : Player, optional
            The player (for future personalization).

        Returns
        -------
        PromptVariant | None
            The selected variant, or None if no variants exist.
        """
        variants = PromptVariant.objects.filter(
            context_type=context_type,
            is_active=True,
        )

        if not variants.exists():
            return None

        best_variant = None
        best_score = -1.0

        for variant in variants:
            # Thompson Sampling: draw from Beta(alpha, beta)
            score = random.betavariate(
                variant.positive_outcomes,
                variant.negative_outcomes,
            )
            if score > best_score:
                best_score = score
                best_variant = variant

        return best_variant

    @classmethod
    def record_outcome(cls, variant_id, was_positive, player_id=None, context_data=None):
        """Record the outcome of a prompt variant usage.

        Parameters
        ----------
        variant_id : int
            The PromptVariant ID.
        was_positive : bool
            Whether the interaction led to a positive outcome.
            Positive = player continued playing, completed next challenge, or
            gave positive feedback. Negative = player left, accuracy dropped,
            or gave negative feedback.
        player_id : int, optional
            The player's ID for tracking.
        context_data : dict, optional
            Additional context about the interaction.
        """
        try:
            variant = PromptVariant.objects.get(id=variant_id)
            if was_positive:
                variant.positive_outcomes += 1
            else:
                variant.negative_outcomes += 1
            variant.save(update_fields=['positive_outcomes', 'negative_outcomes', 'updated_at'])

            PromptOutcomeLog.objects.create(
                variant=variant,
                player_id=player_id or 0,
                was_positive=was_positive,
                context_data=context_data or {},
            )
        except PromptVariant.DoesNotExist:
            logger.warning("PromptVariant %s not found", variant_id)

    @classmethod
    def get_strategy_report(cls, context_type=None):
        """Get performance report for all active variants.

        Returns
        -------
        list[dict]
            Sorted by success rate (descending).
        """
        qs = PromptVariant.objects.filter(is_active=True)
        if context_type:
            qs = qs.filter(context_type=context_type)

        report = []
        for v in qs:
            total = v.positive_outcomes + v.negative_outcomes - 2  # Subtract prior
            report.append({
                'id': v.id,
                'context_type': v.context_type,
                'strategy': v.strategy,
                'success_rate': round(v.success_rate, 3),
                'total_trials': max(0, total),
                'description': v.description,
            })

        report.sort(key=lambda x: x['success_rate'], reverse=True)
        return report

    @classmethod
    def deactivate_underperformers(cls, min_trials=50, min_rate=0.3):
        """Deactivate variants that consistently underperform.

        Parameters
        ----------
        min_trials : int
            Minimum trials before considering deactivation.
        min_rate : float
            Success rate below which to deactivate.
        """
        deactivated = 0
        for v in PromptVariant.objects.filter(is_active=True):
            total = v.positive_outcomes + v.negative_outcomes - 2
            if total >= min_trials and v.success_rate < min_rate:
                v.is_active = False
                v.save(update_fields=['is_active', 'updated_at'])
                deactivated += 1
                logger.info(
                    "Deactivated underperforming variant: %s (rate=%.1f%%)",
                    v, v.success_rate * 100,
                )
        return deactivated
