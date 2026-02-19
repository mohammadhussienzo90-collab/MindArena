"""Feed personalization and delivery."""


class FeedService:

    @classmethod
    def get_personalized_feed(cls, player, page=1, page_size=10):
        """Get personalized feed items for a player."""
        from .models import FeedItem, FeedInteraction

        seen_ids = FeedInteraction.objects.filter(
            player=player,
        ).values_list('feed_item_id', flat=True)

        items = FeedItem.objects.filter(
            is_active=True,
        ).exclude(id__in=seen_ids)

        if player.premium_tier == 'free':
            items = items.filter(is_premium=False)

        # Prioritize weak realms
        weak_realms = cls._get_weak_realms(player)
        if weak_realms:
            from django.db.models import Case, When, IntegerField, Value
            items = items.annotate(
                is_weak_realm=Case(
                    When(realm__slug__in=weak_realms, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-is_weak_realm', '-created_at')
        else:
            items = items.order_by('-created_at')

        offset = (page - 1) * page_size
        return items[offset:offset + page_size]

    @classmethod
    def _get_weak_realms(cls, player):
        """Find player's weakest realms for prioritization."""
        from apps.progression.models import PlayerRealmStat

        stats = list(PlayerRealmStat.objects.filter(player=player).select_related('realm'))
        if not stats:
            return []

        avg_level = sum(s.realm_level for s in stats) / len(stats)
        return [s.realm.slug for s in stats if s.realm_level < avg_level]

    @classmethod
    def mark_interaction(cls, player, feed_item, liked=False, completed=False):
        from .models import FeedInteraction
        interaction, _ = FeedInteraction.objects.update_or_create(
            player=player,
            feed_item=feed_item,
            defaults={'liked': liked, 'completed': completed},
        )

        if completed and feed_item.xp_value > 0:
            from apps.progression.services import XPService
            XPService.award_xp(
                player=player,
                amount=feed_item.xp_value,
                source='feed',
                source_id=feed_item.id,
                realm=feed_item.realm,
            )

        return interaction
