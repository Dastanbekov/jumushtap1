from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Review
from .serializers import ReviewSerializer
from apps.deals.models import Deal
from apps.ratings.services import FraudProtectionService, RatingService


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    Integrates fraud protection and automatic rating recalculation.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Allow filtering by user"""
        queryset = Review.objects.all()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(to_user_id=user_id)
        return queryset

    def perform_create(self, serializer):
        deal = serializer.validated_data['deal']
        user = self.request.user
        rating = serializer.validated_data['rating']
        
        # Validate deal participation
        if user != deal.customer and user != deal.worker:
            raise serializers.ValidationError("You are not part of this deal.")
        
        # Validate deal status
        if deal.status != 'finished':
            raise serializers.ValidationError("Deal is not finished yet.")
        
        # Determine target user
        if user == deal.customer:
            to_user = deal.worker
        else:
            to_user = deal.customer
        
        # Check for duplicate review
        if Review.objects.filter(deal=deal, from_user=user).exists():
            raise serializers.ValidationError("You already reviewed this deal.")
        
        # Run fraud protection checks
        should_block, reason, warnings = FraudProtectionService.run_all_checks(
            from_user=user,
            to_user=to_user,
            deal=deal,
            rating=rating,
            request=self.request
        )
        
        if should_block:
            raise serializers.ValidationError(f"Review blocked: {reason}")
        
        # Get client IP for tracking
        ip_address = FraudProtectionService.get_client_ip(self.request)
        
        # Save review
        review = serializer.save(
            from_user=user, 
            to_user=to_user,
            ip_address=ip_address
        )
        
        # Recalculate rating through service
        RatingService.recalculate_rating(
            user=to_user,
            review=review,
            reason='review_added',
            triggered_by=user
        )
    
    def perform_destroy(self, instance):
        """Handle review deletion with rating recalculation"""
        to_user = instance.to_user
        triggered_by = self.request.user
        
        # Only admin or review author can delete
        if self.request.user != instance.from_user and not self.request.user.is_staff:
            raise serializers.ValidationError("You cannot delete this review.")
        
        instance.delete()
        
        # Recalculate rating after deletion
        RatingService.recalculate_rating(
            user=to_user,
            reason='review_deleted',
            triggered_by=triggered_by
        )
