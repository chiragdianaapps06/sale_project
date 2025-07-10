from django.db import models

from django.contrib.auth.models import AbstractUser

from django.utils import timezone

# Create your models here.
class UserInfo(models.Model):
    
    created_at = models.DateTimeField(auto_created=True)
    updated_at = models.DateField(auto_created= True)


class User(AbstractUser,UserInfo):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150,default=False)
    is_verified = models.BooleanField(default=False,null=False)
    # password = models.CharField(max_length=128, null=True, blank=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username}"
    



class OptVerification(UserInfo , models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    otp = models.IntegerField(max_length=6)
    password = models.CharField(max_length=120)
    

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)







