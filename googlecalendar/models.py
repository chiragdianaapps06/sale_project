from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db import models

class CalendarTimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True 


class GoogleCalendarToken(CalendarTimeStampedModel):

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_uri = models.TextField()
    scopes = models.TextField()

    
