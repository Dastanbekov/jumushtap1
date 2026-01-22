from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import NotificationSettings
from .serializers import NotificationSettingsSerializer

class FCMTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        if not token:
             return Response({"error": "Token required"}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.fcm_token = token
        request.user.save()
        return Response({"status": "FCM Token updated"})

class NotificationSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSettingsSerializer

    def get_object(self):
        obj, created = NotificationSettings.objects.get_or_create(user=self.request.user)
        return obj
