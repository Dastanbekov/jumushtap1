from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

class Rating(models.Model):
    """
    Rating model for 2-way feedback between Worker and Business.
    """
    rater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings_given',
        verbose_name=_('Rater')
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ratings_received',
        verbose_name=_('Reviewee')
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name=_('Job')
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('Score'),
        help_text=_('Score from 1 to 5')
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_('Comment')
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Tags'),
        help_text=_('List of tags e.g. ["punctual", "polite"]')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Rating')
        verbose_name_plural = _('Ratings')
        ordering = ['-created_at']
        unique_together = ['rater', 'job']  # One rating per user per job

    def __str__(self):
        return f"Rating {self.score} for {self.reviewee} by {self.rater}"
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Trigger async or sync update of profile rating
        self.update_profile_rating()

    def update_profile_rating(self):
        """
        Update the average rating in the reviewee's profile.
        """
        # Logic to update user's average rating
        if self.reviewee.is_worker:
            try:
                self.reviewee.worker_profile.update_rating()
            except Exception:
                pass
        elif self.reviewee.is_business:
            try:
                self.reviewee.business_profile.update_rating()
            except Exception:
                pass
