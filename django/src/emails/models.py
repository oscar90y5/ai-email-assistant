from django.db import models


class EmailClassification(models.IntegerChoices):
    SPAM = 1
    IMPORTANT = 2
    NEWSLETTER = 3
    IRRELEVANT = 4


class Email(models.Model):
    gmail_id = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=500)
    sender = models.CharField(max_length=255)
    snippet = models.TextField()
    received_at = models.DateTimeField()
    processed_at = models.DateTimeField(null=True, blank=True)
    classification = models.IntegerField(
        choices=EmailClassification.choices,
        null=True,
        blank=True,
    )
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"[{self.get_classification_display()}] {self.subject} — {self.sender}"
