from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Rating
from .serializers import RatingSerializer

class RatingViewSet(viewsets.ModelViewSet):
    """
    CRUD for ratings. 
    Usually users just Create (POST) ratings. 
    Reading (GET) is allowed to see own ratings or others (public).
    """
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can see ratings they gave or received
        user = self.request.user
        return Rating.objects.filter(reviewee=user) | Rating.objects.filter(rater=user)
        
    def perform_create(self, serializer):
        serializer.save(rater=self.request.user)
