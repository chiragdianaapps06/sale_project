
from django.shortcuts import render

from rest_framework.response import Response 
from rest_framework import status
from rest_framework import viewsets

from .serializers import SignUpSerializer ,OtpVerificationSerializer, UpdateProfileSerializer ,UserModelSerilizer

from rest_framework.views import APIView
from .models import OtpVerification
from django.contrib.auth import get_user_model

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from rest_framework.exceptions import APIException

# Send OTP to user's registered email
from .tempserializer import OtpVerificationMixin

# paginations import
from rest_framework.pagination import PageNumberPagination

# importing for csv file dowload functionality
import pandas as pd
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.decorators import api_view , permission_classes
import csv
from django.http import StreamingHttpResponse
from ordering.models import Order

# importing logger
from ordering.logger import get_logger

logger = get_logger("csv_download_logger")


User = get_user_model()




'''Signup View'''


class SignUpView(viewsets.ModelViewSet):

    '''
        View to handle signup and send otp to email for verification.
    '''
    queryset = User.objects.all()
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):

        try:
            if User.objects.filter(username = request.data['username']).exists():
                return Response({
                    "message": "User with this username already exists.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            User.objects.get(email= request.data['email'])
            # User.objects.get(username = request.data['username'])
            return Response({"message":"user already exist", "data": None},status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist: 
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():

                self.request.session['password'] = serializer.validated_data['password']
                serializer.save()
                return Response(
                    {
                        "message": "OTP sent to email. Please verify to complete registration.",
                        "data":None
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {
                    "message": str(e),
                    "data": None
                }
                , status=status.HTTP_400_BAD_REQUEST
                )
        
        
'''Otp Verification View'''

class OtpVerificationsView(APIView):
    
    """
        View to handle OTP verification for new user signup.
    """

    def post(self, request):
        password = request.session.get('password')
        serializer = OtpVerificationSerializer(data=request.data, context={'password': password})
        

        try:

            if serializer.is_valid():
                # print("=====",serializer.save())
                serializer.save()
                

                return Response(
                    {"message": "User registered successfully!",
                     "data":None},
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:

            return Response({"message": str(e), "data": None}, status=status.HTTP_400_BAD_REQUEST)
    

'''Login View'''

class LoginView(APIView):
    
    '''
        View to hanlde user login using Jwt authentication.
    '''

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

        user = authenticate(email=email, password=password)

        if user is None:
            return Response({'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)
        print(user.email)

        refresh = RefreshToken.for_user(user)
        print(refresh)
        print(refresh.access_token)
        return Response({
            'message': 'User logged in successfully.',
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token),
            'email':user.email
        }, status=status.HTTP_200_OK)





'''Protected View for testing'''


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated"})
    


''' Logout View '''

class LogoutView(APIView):

    """
        View to handle logout by blacklisting the refresh token.
    """

    permission_classes = [IsAuthenticated]

    def post(self,request):
        try:
            refresh_token  = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message":"User logged out Success", },status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            return Response({"message":"Invalid Token or Token Expired", "data": None},status=status.HTTP_400_BAD_REQUEST)



'''Update Profile View '''



# class UpdateProfileView(generics.UpdateAPIView):

#     """
#         View to allow users to update their profile information.
#         Triggers OTP if email is being changed.
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = UpdateProfileSerializer
#     queryset = User.objects.all()

#     def get_object(self):
#         return self.request.user

#     def update(self, request, *args, **kwargs):
#         serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()

#         if request.data.get('email') and request.data['email'] != self.request.user.email:
#             return Response({"message": "OTP sent to new email. Please verify to complete email update."})

#         return Response({"message": "Profile updated successfully."})


class UpdateProfileView(generics.UpdateAPIView):
    """
    View to allow users to update their profile information.
    Triggers OTP if email is being changed.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateProfileSerializer
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_email = instance.email

        serializer = self.get_serializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Check if there's anything to update
        if not serializer.validated_data:
            return Response({"message": "No changes detected."}, status=status.HTTP_200_OK)

        user = serializer.save()
        new_email = request.data.get('email')

        if new_email and new_email != old_email:
            return Response(
                {"message": "OTP sent to new email. Please verify to complete email update."},
                status=status.HTTP_200_OK
            )

        return Response({"message": "Profile updated successfully.","data":serializer.data}, status=status.HTTP_200_OK)



'''verify email change view'''


class VerifyEmailChangeOtpView(APIView):
    
    """
        Verifies OTP for email change and updates user's email.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OtpVerificationSerializer(data=request.data, context={
            'request': request,
            'action': 'update_email'
        })

        if serializer.is_valid():
            serializer.update(instance=request.user, validated_data={})
            return Response({"message": "Email updated successfully."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

    

'''Update Password View'''




class UpdatePasswordView(APIView):

    """
        Sends OTP to registered email for password change and stores new password in session.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
      

        mixin = OtpVerificationMixin()


        password = request.data.get('password')
        confirmed_password = request.data.get('confirmed_password')
        old_password = request.data.get('old_password')
        
        # 1. Check that password and confirmed password match
        if password != confirmed_password:
            return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Validate old password
        user = request.user
        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        
        if old_password == password:
            return Response({"No change: pass new password. "})
        

        mixin.generate_and_send_otp(email=request.user.email, username=request.user.username)

        # Store new password temporarily in session
        request.session['pending_password'] = password
        request.session['confirmed_password'] = confirmed_password
        request.session['old_password'] = old_password

        return Response({"message": "OTP sent to your registered email. Please verify to update password."})



'''verift password change view'''

class VerifyPasswordChangeOtpView(APIView):

    """
        Verifies OTP and updates the user's password.
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.session.get('pending_password')
        confirmed_password = request.session.get('confirmed_password')
        old_password = request.session.get('old_password')

        if not (password and confirmed_password and old_password):
            return Response({"error": "Session expired or password data missing."}, status=status.HTTP_400_BAD_REQUEST)
        
        if password != confirmed_password:
            return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)

        

        # 2. Validate old password
        user = request.user
        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        

        otp_serializer = OtpVerificationSerializer(data=request.data, context={
            'request': request,
            'action': 'update_password',
            'password': password
        })

        if otp_serializer.is_valid():
            otp_serializer.update(instance=request.user, validated_data={})

            # Clear session
            request.session.pop('pending_password', None)
            request.session.pop('confirmed_password', None)
            request.session.pop('old_password', None)

            return Response({"message": "Password updated successfully."})
        return Response(otp_serializer.errors, status=status.HTTP_400_BAD_REQUEST)







class ActivateDeactivateUserView(APIView):
    from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class ActivateDeactivateUserView(APIView):

    # Admin can activate and deactivate any agent 
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            route_name = request.resolver_match.url_name  # Get route name

            # Decide based on route
            if route_name == 'user-activate-view':
                if user.is_active:
                    return Response({
                        "status": False,
                        "message": "User is already active."
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.is_active = True
                user.save()
                return Response({
                    "status": True,
                    "message": "User activated successfully.",
                    "user_id": user.id,
                    "is_active": user.is_active
                }, status=status.HTTP_200_OK)

            elif route_name == 'user-deavtivate-view':
                if not user.is_active:
                    return Response({
                        "status": False,
                        "message": "User is already inactive."
                    }, status=status.HTTP_400_BAD_REQUEST)
                user.is_active = False
                user.save()
                return Response({
                    "status": True,
                    "message": "User deactivated successfully.",
                    "user_id": user.id,
                    "is_active": user.is_active
                }, status=status.HTTP_200_OK)

            return Response({
                "status": False,
                "message": "Invalid action."
            }, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({
                "status": False,
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)



class AdminUserListApiView(APIView):


    '''
    API view to list all non-superuser users.
    Only admin users are allowed to access this endpoint.
    '''

    permission_classes = [IsAdminUser]

    def get(self,request):
        try:

            users = User.objects.exclude(is_superuser=True)
            paginator = PageNumberPagination()
            paginator.page_size = 10
            paginated_users = paginator.paginate_queryset(users,request)
            serilizer = UserModelSerilizer(paginated_users,many=True)

            return paginator.get_paginated_response(serilizer.data)

        except Exception as e:
            return Response({
                "message": "An unexpected error occurred while listing users.",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




@api_view(http_method_names=['GET'])
def export_data(request):
    print(request.user)
    
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to access this file.")
    
    user = User.objects.values('id','email','username','first_name','last_name','is_active','is_superuser')
    df  = pd.DataFrame(list(user))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename=persons.csv'
    df.to_csv(response,index=False, lineterminator='\n')
    return response



class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        return value
    
@api_view(http_method_names=['GET'])
@permission_classes([IsAdminUser])
def export_data_optimize(request):
    try:

        rows = User.objects.values_list('id','email','username','first_name','last_name','is_active','is_superuser').iterator()

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        # Generator expression for streaming
        def row_generator():
            yield ['id','email','username','first_name','last_name','is_active','is_superuser']  # headers
            for row in rows:
                yield row
            
            logger.info("Finished generating CSV rows.")

        response = StreamingHttpResponse(
            (writer.writerow(row) for row in row_generator()),
            content_type='text/csv'
        )
        response['Content-Disposition'] = 'attachment; filename="large_users.csv"'
        logger.info("CSV export completed successfully.")

        return response
    
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}", exc_info=True)
        return Response(
            {"error": "An error occurred while exporting the CSV."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    



    
@api_view(http_method_names=['GET'])
@permission_classes([IsAdminUser])
def export_large_user_csv(request):
    """
    Exports a large dataset of Orders as CSV using streaming response.
    Admin-only access. Handles exceptions with proper logging and JSON error.
    """
    try:
        rows = Order.objects.values_list('order_id', 'agent', 'item_type', 'order_date','country').iterator()
        # rows = Order.objects.all()

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        # Generator expression for streaming
        
        def row_generator():
            i=0
            yield ['order_id', 'agent', 'item_type', 'order_date','country']  # headers
            for row in rows:
                print("=====",i)
                i+=1
                yield row
            logger.info("Finished generating CSV rows.")

        response = StreamingHttpResponse(
            (writer.writerow(row) for row in row_generator()),
            content_type='text/csv'
        )
        response['Content-Disposition'] = 'attachment; filename="order_data_large.csv"'

        logger.info("CSV export completed successfully.")

        return response

    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}", exc_info=True)
        return Response(
            {"error": "An error occurred while exporting the CSV."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )