from django.db import models

from django.contrib.auth.models import AbstractUser

from django.utils import timezone

class TimestampModel(models.Model):
    createdAt=models.DateTimeField(auto_now_add=True)
    updatedAt=models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True



# class UserTimeStamp(models.Model):
    
#     created_at = models.DateTimeField(default=timezone.now)
#     updated_at = models.DateTimeField(default=timezone.now)
    # class Meta:
    #     abstract = True


class User(AbstractUser,TimestampModel):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150,default=False)
    is_verified = models.BooleanField(default=False,null=False)
    # password = models.CharField(max_length=128, null=True, blank=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username}"
    



class OtpVerification(TimestampModel):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150)
    otp = models.IntegerField()
    
    

    def is_expired(self):
        return timezone.now() > self.updatedAt + timezone.timedelta(minutes=5)







