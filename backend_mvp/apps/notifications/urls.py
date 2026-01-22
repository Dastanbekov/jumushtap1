from django.urls import path
from .views import FCMTokenView, NotificationSettingsView

urlpatterns = [
    path('notifications/fcm/', FCMTokenView.as_view(), name='fcm_token'),
    path('notifications/settings/', NotificationSettingsView.as_view(), name='notification_settings'),
]
