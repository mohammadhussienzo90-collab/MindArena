from django.db import models


class FeedItem(models.Model):
    CONTENT_TYPES = [
        ('tip', 'Quick Tip'),
        ('fact', 'Interesting Fact'),
        ('challenge', 'Mini Challenge'),
        ('quote', 'Motivational Quote'),
        ('lesson', 'Micro Lesson'),
        ('reflection', 'Reflection Prompt'),
    ]
    slug = models.CharField(max_length=100, unique=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    realm = models.ForeignKey('realms.Realm', on_delete=models.CASCADE, related_name='feed_items', null=True, blank=True)
    title_en = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200, blank=True)
    body_en = models.TextField()
    body_ar = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    difficulty = models.SmallIntegerField(default=1)
    xp_value = models.IntegerField(default=5)
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title_en


class FeedInteraction(models.Model):
    player = models.ForeignKey('accounts.Player', on_delete=models.CASCADE, related_name='feed_interactions')
    feed_item = models.ForeignKey(FeedItem, on_delete=models.CASCADE)
    seen = models.BooleanField(default=True)
    liked = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    seen_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['player', 'feed_item']
