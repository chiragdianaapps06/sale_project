from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import (  SignUpView , OtpVerificationsView , LoginView , 
                    ProtectedView, LogoutView , UpdateProfileView,
                    UpdatePasswordView , VerifyEmailChangeOtpView, VerifyPasswordChangeOtpView,
                    ActivateDeactivateUserView, AdminUserListApiView ,export_data ,export_data_optimize ,
                    export_large_user_csv)


# from .tempview import (  SignUpView , OtpVerificationsView , LoginView , 
#                     ProtectedView, LogoutView , UpdateProfileView,
#                     UpdatePasswordView , VerifyEmailChangeOtpView , VerifyPasswordChangeOtpView)
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

routers = DefaultRouter()
routers.register(r'register',SignUpView,basename='register')



urlpatterns = [
     path('register/otp/',OtpVerificationsView.as_view(),name="otp-verification"),
     path('login/',LoginView.as_view(),name = "login"),

     path('generate-token/',TokenRefreshView.as_view(),name="refresh-access-token"),
     path('protected/',ProtectedView.as_view(),name="protected-view"),

     path('logout/',LogoutView.as_view(),name = "logout"),
     path('update-profile/',UpdateProfileView.as_view(),name ='update-profile'),
     path('update-profile/verify-email/',VerifyEmailChangeOtpView.as_view(),name='update-email-verify'),

     # path('update-password/<int:pk>/',UpdatePasswordView.as_view(),name = 'update_password')

     path('update-password/send-otp/', UpdatePasswordView.as_view()),
     path('update-password/verify-otp/', VerifyPasswordChangeOtpView.as_view()),

     path('deactivate/<int:user_id>/',ActivateDeactivateUserView.as_view(),name='user-deavtivate-view'),
     path('activate/<int:user_id>/',ActivateDeactivateUserView.as_view(),name='user-activate-view'),
     # path('activate/<int:user_id>/',ActivateDeactivateUserView.as_view(),name='user-activate-deactivate-view'),
     path('listuser/',AdminUserListApiView.as_view(),name='listuser-admin-view'),


     # url for User data csv download
     path('download/',export_data,name="download-user-data"),
     path('download-optimize/',export_data_optimize,name="download-user-data-optimize"),
  

     # url for  order data csv download
     path('download/orders/',export_large_user_csv,name="download-order-data"),


   
     
]+routers.urls



