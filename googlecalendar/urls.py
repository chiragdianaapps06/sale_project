from django.urls import path
from  .views import GoogleAuthInitView,GoogleAuthCallbackView,GoogleCalendarEventsView,FetchFreeMeetingSlot

urlpatterns = [
    path('google/init/', GoogleAuthInitView.as_view(), name='google-init'),
    path('google/callback/', GoogleAuthCallbackView.as_view(), name='google-callback'),
    path('google/event-list/', GoogleCalendarEventsView.as_view(), name='goole-calendar-list-event'),
    path('google/free-slot/', FetchFreeMeetingSlot.as_view(), name='goole-calendar-slot'),
    
]
