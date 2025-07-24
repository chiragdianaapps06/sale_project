from django.urls import path
from  .views import GoogleAuthInitView,GoogleAuthCallbackView

urlpatterns = [
    path('google/init/', GoogleAuthInitView.as_view(), name='google-init'),
    path('google/callback/', GoogleAuthCallbackView.as_view(), name='google-callback'),
]
