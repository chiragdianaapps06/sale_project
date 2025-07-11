from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import SignUpView , OtpVerificationsView , LoginView , ProtectedView
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

routers = DefaultRouter()
routers.register(r'register',SignUpView,basename='register')



urlpatterns = [
     path('register/otp/',OtpVerificationsView.as_view(),name="otp-verification"),
     path('login/',LoginView.as_view(),name = "login"),
     path('generate-token/',TokenRefreshView.as_view(),name="refresh-access-token"),
     path('protected/',ProtectedView.as_view(),name="protected-view")

   
     
]+routers.urls



