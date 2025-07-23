from django.shortcuts import render
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .utils import get_private_group_name
from .models import *
from .serilizers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

User = get_user_model()
class ChatMessagesView(APIView):

    ''' view that provide all chat betwenn two user '''

    permission_classes = [IsAuthenticated]

    def get(self, request,username):
        try:
            receiver = User.objects.get(username= username)
            group_name = get_private_group_name(self,request.user , receiver)
            chat_group = ChatGroup.objects.get(group_name=group_name)

        except User.DoesNotExist:
            return Response({"message":"user not exist"})
        
        except ChatGroup.DoesNotExist:
            return Response({"message":"No chat started yet."})
    
        messages = ChatMessages.objects.filter(room = chat_group).order_by('time_stamp')
        serializer = ChatMessagesSerializer(messages, many = True)
        return Response({"message":"get messages history successfully.","data" :serializer.data}, status=status.HTTP_200_OK)
