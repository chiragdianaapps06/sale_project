from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from django.utils import timezone

User = get_user_model()


from .models import OtpVerification
import random 
from django.core.mail import send_mail

from rest_framework.views import APIView



class SignUpSerializer(serializers.Serializer):


    email = serializers.EmailField()
    username = serializers.CharField()
    # password = serializers.CharField(write_only = True)
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])


    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data



    def create(self,validated_data):
        
        otp = str(random.randint(100000,999999))

        
        OtpVerification.objects.update_or_create(   
            email=validated_data['email'],
            defaults={
                'username': validated_data['username'],
                'password': validated_data['password'],  
                'otp': otp
            }
        )



        send_mail(
            'your opt code',
            f'your otp is {otp}',
            'noreply@example.com',
            [validated_data['email']],
            fail_silently=False
        )
        print(f"opt send to {validated_data['email']} , otp is {otp}")

        return validated_data


class OtpVarificationSerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField()


    def validate(self,data):
        try:
            record = OtpVerification.objects.get(email =data['email'] ,otp =data['otp'] )

            print("opt verification",record)

        except OtpVerification.DoesNotExist:
            raise serializers.ValidationError("email or opt does not exist")
        
        print("OTP created at:", record.createdAt)
        print("Now:", timezone.now())
        print("Is expired:", record.is_expired())
        if  record.is_expired():
            raise serializers.ValidationError("opt expired.")
        
        return data
        


    def create(self, validated_data):
        record = OtpVerification.objects.get(email = validated_data['email'])

        user = User.objects.create_user(
            email=record.email,
            username=record.username,
            password=record.password
        )
        user.is_verified = True
        user.save()

        
        record.delete()

        return user
    

