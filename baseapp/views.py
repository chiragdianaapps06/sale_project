
from django.shortcuts import render

from rest_framework.response import Response 
from rest_framework import status
from rest_framework import viewsets

from .serializers import SignUpSerializer ,OtpVarificationSerializer  , UpdateProfileSerializer , UpdatePasswordSerializer

from rest_framework.views import APIView
from .models import OtpVerification
from django.contrib.auth import get_user_model

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException


User = get_user_model()



'''Signup View'''


class SignUpView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):

        try:

            User.objects.get(email= request.data['email'])
            return Response({"message":"user already exist"},status=status.HTTP_400_BAD_REQUEST)
        
        except User.DoesNotExist: 
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():

                self.request.session['password'] = serializer.validated_data['password']
                serializer.save()
                return Response(
                    {"message": "OTP sent to email. Please verify to complete registration."},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
'''Otp Verification View'''

class OtpVerificationsView(APIView):

    def post(self, request):
        password = request.session.get('password')
        serializer = OtpVarificationSerializer(data=request.data, context={'password': password})
        
        if serializer.is_valid():
            print("=====",serializer.save())
            serializer.save()
            

            return Response(
                {"message": "User registered successfully!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

'''Login View'''

class LoginView(APIView):
    

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
    permission_classes = [IsAuthenticated]

    def post(self,request):
        try:
            refresh_token  = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message":"User logged out Success"},status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            return Response({"message":"Invalid Token or Token Expired"},status=status.HTTP_400_BAD_REQUEST)



'''Update Profile View '''

class UpdateProfileView(generics.UpdateAPIView):

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateProfileSerializer

    # http_method_names = ['patch']

    # thhis is make sure that only authenticated duser can update their profile

    def get_object(self):
        return self.request.user
    

    

'''Update Password View'''

class UpdatePasswordView(generics.UpdateAPIView):

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UpdatePasswordSerializer


    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):

        try:

            serializer = self.get_serializer(instance=self.get_object(), data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({"message": "Password updated successfully."}, status=status.HTTP_205_RESET_CONTENT)
        
        except APIException as api_error:
            return Response({"error": str(api_error.detail)}, status=api_error.status_code)
        except Exception as e:
            return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)



