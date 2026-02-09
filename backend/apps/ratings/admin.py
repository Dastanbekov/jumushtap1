from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'rater', 'reviewee', 'job', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['rater__phone', 'reviewee__phone', 'job__title']
    readonly_fields = ['created_at', 'updated_at']
