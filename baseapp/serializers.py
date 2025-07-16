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




from rest_framework import serializers

class OtpVerificationMixin:

    """
    Mixin to provide OTP generation and verification logic for serializers.
    """


    def generate_and_send_otp(self,email,username = None):

        '''Generate a random 6 digit otp , store it to otpverification db and send it to email'''

        # generate 6 digit random otp
        otp = str(random.randint(100000,999999))

        # save/update otp to db 
        OtpVerification.objects.update_or_create(   
            email=email,
            defaults={
                'username': username,
                # 'password': validated_data['password'],  
                'otp': otp
            }
        )


        # send otp mail
        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP is {otp}',
            from_email='noreply@example.com',
            recipient_list=[email],
            fail_silently=False,
        )
        print(f"opt send to {email} , otp is {otp}")

        return otp

    def verify_otp(self, email, otp):

        """
        Verifies that the given OTP for the email is valid and not expired.
        """
        try:
            record = OtpVerification.objects.get(email=email, otp=otp)
        except OtpVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid email or OTP")

        if record.is_expired():
            raise serializers.ValidationError("OTP has expired")

        return record  # Valid OTP record




'''Signup serilizer'''





class SignUpSerializer(serializers.Serializer, OtpVerificationMixin):
    
    """
    Serializer for signing up users. It validates passwords and
    triggers OTP generation and email delivery.
    """

    email = serializers.EmailField()
    username = serializers.CharField()
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate(self, data):
        '''
         Ensure that password and comfirm_password firld match
        '''

        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        
        '''
            Trigger Oip generation and send mail
        '''
        self.generate_and_send_otp(validated_data['email'], validated_data['username'])
        return validated_data


'''Otp verification serializer'''

class OtpVerificationSerializer(serializers.Serializer, OtpVerificationMixin):
    
    """
        Serializer to verify OTP sent to the user's email for either signup or update actions.
    """
        
    email = serializers.EmailField()
    otp = serializers.CharField()

    def validate(self, data):
        '''
             Verify that otp is valid or not expired.
        '''
        record = self.verify_otp(data['email'], data['otp'])
        self.record = record
        return data

    def create(self, validated_data):
        '''
            creating new user after verification during signup.
        '''

        record = self.record
        password = self.context.get('password')


        if not record or not record.id:
            raise serializers.ValidationError("OTP verification record not found or not saved properly")

        user, created = User.objects.get_or_create(
            email=record.email,
            defaults={'username': record.username, 'is_verified': True}
        )
        if password:
            user.set_password(password)
        user.save()
        record.delete()
        return user

    def update(self, instance, validated_data):
        
        """
            Handles OTP-based updates like changing the email or password.
        """
        record = self.record
        action = self.context.get('action')


        if not record or not record.id:
            raise serializers.ValidationError("OTP verification record not found or not saved properly")

        if action == 'update_email':
            instance.email = record.email
        elif action == 'update_password':
            password = self.context.get('password')
            instance.set_password(password)

        instance.save()
        record.delete()
        return instance

   
    



'''Update profile serilizer'''


class UpdateProfileSerializer(serializers.ModelSerializer, OtpVerificationMixin):
    
    """
        Serializer for updating user profile fields (username, first_name, last_name, email).
        If the email is changed, triggers an OTP process instead of updating it immediately.
    """
     
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
            'username': {'required': False}
        }

    def validate_email(self, email):
        '''
            Ensuring that new email shoulf be unique.
        '''
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            raise serializers.ValidationError("This email is already in use by another user")
        return email

    def validate_username(self, username):
        
        '''
            Ensuring that new email shoulf be unique.
        '''
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=username).exists():
            raise serializers.ValidationError("This username is already taken")
        return username

    def update(self, instance, validated_data):
        
        email = validated_data.get('email')

        # If email is changing, trigger OTP and skip applying the email update for now
        if email and email != instance.email:
            self.generate_and_send_otp(email, instance.username)
            return instance  # Do not update email here

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)

        instance.save()
        return instance

