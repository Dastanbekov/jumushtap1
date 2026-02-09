from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class SuspiciousActivity(models.Model):
    """
    Log of suspicious activities flagged by the system.
    """
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suspicious_activities',
        verbose_name=_('User')
    )
    reason = models.CharField(max_length=255, verbose_name=_('Reason'))
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        verbose_name=_('Severity')
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Details'),
        help_text=_('Snapshot of relevant data/evidence')
    )
    is_resolved = models.BooleanField(default=False, verbose_name=_('Resolved'))
    resolution_notes = models.TextField(blank=True, verbose_name=_('Resolution Notes'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Suspicious Activity')
        verbose_name_plural = _('Suspicious Activities')
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.user} - {self.reason}"
