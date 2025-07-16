
from django.shortcuts import render

from rest_framework.response import Response 
from rest_framework import status
from rest_framework import viewsets

from .serializers import SignUpSerializer ,OtpVerificationSerializer, UpdateProfileSerializer 

from rest_framework.views import APIView
from .models import OtpVerification
from django.contrib.auth import get_user_model

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException

# Send OTP to user's registered email
from .tempserializer import OtpVerificationMixin


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
            
            "data":{
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token),
            },
            'message': 'User logged in successfully.',
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

            return Response({"message":"User logged out Success", "data": None},status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            return Response({"message":"Invalid Token or Token Expired", "data": None},status=status.HTTP_400_BAD_REQUEST)



'''Update Profile View '''



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
        serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if request.data.get('email') and request.data['email'] != self.request.user.email:
            return Response({"message": "OTP sent to new email. Please verify to complete email update."})

        return Response({"message": "Profile updated successfully."})



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
        mixin.generate_and_send_otp(email=request.user.email, username=request.user.username)

        # Store new password temporarily in session
        request.session['pending_password'] = request.data.get('password')
        request.session['confirmed_password'] = request.data.get('confirmed_password')
        request.session['old_password'] = request.data.get('old_password')

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
            return Response({"error": "Session expired or password data missing."}, status=400)

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
        return Response(otp_serializer.errors, status=400)






