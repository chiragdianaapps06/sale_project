from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import SignUpView
from . import views

routers = DefaultRouter()
routers.register(r'register',SignUpView,basename='register')



urlpatterns = [
     path('register/otp/',views.OtpVerificationsView,name="otp-verification")
     
]+routers.urls
