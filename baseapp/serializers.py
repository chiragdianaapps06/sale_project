from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()


from .models import OtpVerification
import random 
from django.core.mail import send_mail
from rest_framework.views import APIView






'''Signup serilizer'''

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
                # 'password': validated_data['password'],  
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




'''Otp verification serializer'''


class OtpVarificationSerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField()
    # password = serializers.CharField(write_only=True, validators=[validate_password])


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

        password =self.context.get('password')

        user = User.objects.update_or_create(
            email=record.email,
            username=record.username,
            password=password

        )
        user.is_verified = True
        user.save()

        
        record.delete()

        return user
    



'''Update Password serilizer'''
class UpdateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields  = ("username","first_name","last_name","email")

        extra_kwargs = {
            'first_name': {'required':False},
            'last_name': {'required': False},
            'email': {'required':False},
            'username':{'required':False}
        }


    def validate_email(self,email):

        user = self.context['request'].user

        if User.objects.exclude(pk =user.pk).filter(email = email).exists():
            raise serializers.ValidationError({'email':'this email is already user by another user'})
        
        return email
    
    def validate_username(self,username):

        user = self.context['request'].user

        if User.objects.exclude(pk = user.pk).filter(username = username).exists():
            raise serializers.ValidationError({'username':'username is already in used'})
        
        return username
    

    def update(self,instance,validated_data):

        try:
            
            instance.first_name = validated_data.get('first_name',instance.first_name)
            instance.last_name  = validated_data.get('last_name',instance.last_name)
            instance.email = validated_data.get('email',instance.email)
            instance.username = validated_data.get('username',instance.username)

            instance.save()

            return instance
        except Exception as e:
            raise serializers.ValidationError({"detail": f"An error occurred: {str(e)}"})


'''Update Password Serializer'''

class UpdatePasswordSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only = True, required = True, validators = [validate_password])
    confirmed_password = serializers.CharField(write_only = True, required = True)
    old_password = serializers.CharField(write_only=True, required=True)


    class Meta:
        model = User
        fields = ('password','confirmed_password','old_password')

    
    def validate(self, data):

        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    

    def validate_old_password(self, value):

        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value


    def update(self, instance, validated_data):

        try:
            instance.set_password(validated_data['password'])
            instance.save()
            return instance
        
        except Exception as e:
            raise serializers.ValidationError({"detail": f"An error occurred: {str(e)}"})

        

