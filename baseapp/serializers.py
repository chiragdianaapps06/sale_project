from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


from .models import OptVerification
import random 
from django.core.mail import send_mail


# class SignUpSerializer(serializers.ModelSerializer):

#     confirm_password = serializers.CharField(write_only=True)
#     password = serializers.CharField(write_only=True, validators=[validate_password])

#     class Meta:
#         model = User
#         fields = ['email', 'username', 'password', 'confirm_password']

#     def validate(self, data):
#         if data['password'] != data['confirm_password']:
#             raise serializers.ValidationError("Passwords do not match")
#         return data

#     def create(self, validated_data):
#         validated_data.pop('confirm_password')
            
#         email = validated_data.get('email')
#         username = validated_data.get('username')
#         password = validated_data.get('password')


#         user = User.objects.create_user(
#             email=email,
#             username=username,
#             password=password
#         )
#         return user
    

class SignUpSerializer(serializers.Serializer):


    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(write_only = True)
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])


    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data



    def create(self,validated_data):
        
        otp = str(random.randint(100000,999999))

        OptVerification.objects.update_or_create(   
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
        return validated_data


class OtpVarificationSerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField()


    def validate(self,data):
        try:
            record = OptVerification.objects.get(email =data['email'] ,otp =data['otp'] )

        except OptVerification.DoesNotExist:
            raise serializers.ValidationError("email or opt does not exist")
        
        if  record.is_expired():
            raise serializers.ErrorDetail("opt expired.")
        
        return data
        


    def create(self, validated_data):
        record = OptVerification.objects.get(email = validated_data['email'])

        user = User.objects.create_user(
            email=record.email,
            username=record.username,
            password=record.password
        )
        user.is_verified = True
        user.save()

        
        record.delete()

        return user