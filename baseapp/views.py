
from django.shortcuts import render

from rest_framework.response import Response 
from rest_framework import status
from rest_framework import viewsets

from .serializers import SignUpSerializer ,OtpVarificationSerializer

from rest_framework.views import APIView

from django.contrib.auth import get_user_model
User = get_user_model()

class SignUpView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "opt send  successfully."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class OtpVerificationsView(APIView):

    def post(self,request):
        serializer = OtpVarificationSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message':"Register user successfully"},
                status = status.HTTP_201_CREATED,    
            )
        
        return Response(serializer.errros,status=status.HTTP_400_BAD_REQUEST)




        




   




        


# from rest_framework.generics import CreateAPIView
# from rest_framework.permissions import AllowAny
# from django.contrib.auth import get_user_model
# from .serializers import SignUpSerializer

# User = get_user_model()

# class SignUpView(CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = SignUpSerializer
#     # permission_classes = [AllowAny]
