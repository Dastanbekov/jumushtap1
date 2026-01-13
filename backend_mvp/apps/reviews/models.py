from django.db import models
from django.conf import settings
from apps.deals.models import Deal

class Review(models.Model):
    deal = models.OneToOneField(Deal, on_delete=models.CASCADE)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviews_given', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviews_received', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update user rating
        reviews = Review.objects.filter(to_user=self.to_user)
        total = sum([r.rating for r in reviews])
        count = reviews.count()
        if count > 0:
            self.to_user.rating = total / count
            self.to_user.save()
