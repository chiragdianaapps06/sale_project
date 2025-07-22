from rest_framework import serializers
from .models import ChatMessages

class ChatMessagesSerializer(serializers.ModelSerializer):
    
    class Meta:
        model =  ChatMessages
        fields = '__all__'
    