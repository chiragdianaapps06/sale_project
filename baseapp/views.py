
from django.shortcuts import render

from rest_framework.response import Response 
from rest_framework import status
from rest_framework import viewsets

from .serializers import SignUpSerializer ,OtpVarificationSerializer

from rest_framework.views import APIView
from .models import OtpVerification
from django.contrib.auth import get_user_model

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny

from rest_framework.permissions import IsAuthenticated


User = get_user_model()

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
                serializer.save()
                return Response(
                    {"message": "OTP sent to email. Please verify to complete registration."},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        


class OtpVerificationsView(APIView):

    def post(self, request):
        serializer =OtpVarificationSerializer(data=request.data)
        print
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


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









class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated"})
    