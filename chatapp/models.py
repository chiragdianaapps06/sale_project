from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=120, unique=True)
    sender =  models.ForeignKey(User,on_delete=models.CASCADE, related_name="sender_messages")
    receiver = models.ForeignKey(User,on_delete=models.CASCADE, related_name="receiver_messages")

    class Meta:
        unique_together = ('sender','receiver')
       

    def __str__(self):
        return f"Chat between {self.sender.username} and {self.receiver.username}"


class ChatMessages(models.Model):
    room = models.ForeignKey(ChatGroup,on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete= models.CASCADE)
    message = models.TextField()
    time_stamp = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f" {self.sender.username} - {self.message[:20]}"
    