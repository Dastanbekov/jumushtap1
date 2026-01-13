from rest_framework import viewsets, permissions, serializers
from .models import Review
from .serializers import ReviewSerializer
from apps.deals.models import Deal

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        deal = serializer.validated_data['deal']
        user = self.request.user
        
        if user != deal.customer and user != deal.worker:
            raise serializers.ValidationError("You are not part of this deal.")
        
        if deal.status != 'finished':
            raise serializers.ValidationError("Deal is not finished yet.")
            
        if user == deal.customer:
            to_user = deal.worker
        else:
             to_user = deal.customer
             
        if Review.objects.filter(deal=deal, from_user=user).exists():
            raise serializers.ValidationError("You already reviewed this deal.")

        serializer.save(from_user=user, to_user=to_user)
