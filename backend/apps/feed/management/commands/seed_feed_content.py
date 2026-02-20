"""
Management command to seed feed content from JSON data.
Usage: python manage.py seed_feed_content [--clear]
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.feed.models import FeedItem
from apps.realms.models import Realm


DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "feed_content.json"


class Command(BaseCommand):
    help = "Seed feed content items from feed_content.json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Clear existing feed items before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            FeedItem.objects.all().delete()
            self.stdout.write(self.style.WARNING("All feed items cleared."))

        # Load JSON data
        if not DATA_FILE.exists():
            self.stderr.write(self.style.ERROR(f"Data file not found: {DATA_FILE}"))
            return

        with open(DATA_FILE, encoding="utf-8") as f:
            feed_data = json.load(f)

        # Build realm lookup
        realms = {r.slug: r for r in Realm.objects.all()}

        created = 0
        updated = 0
        skipped = 0

        for item in feed_data:
            realm_slug = item.get("realm_slug")
            realm = realms.get(realm_slug)

            if realm_slug and not realm:
                self.stdout.write(self.style.WARNING(
                    f"  Realm '{realm_slug}' not found, skipping '{item['slug']}'."
                ))
                skipped += 1
                continue

            _, was_created = FeedItem.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "title_en": item["title_en"],
                    "title_ar": item.get("title_ar", ""),
                    "body_en": item["body_en"],
                    "body_ar": item.get("body_ar", ""),
                    "content_type": item["content_type"],
                    "realm": realm,
                    "xp_value": item.get("xp_value", 5),
                    "is_premium": item.get("is_premium", False),
                    "is_active": True,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Feed content seeded: {created} created, {updated} updated, {skipped} skipped."
        ))
