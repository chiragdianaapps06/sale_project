from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import ChatGroup , ChatMessages
from .utils import get_private_group_name
from django.core.exceptions import ObjectDoesNotExist


User = get_user_model()

class PrivateChatConsumer(AsyncWebsocketConsumer):
    '''
    Websocket consumer for private one to one chat 
    '''

    async def connect(self):
        '''
        Handle WebSocket connection.
        Identify the current user and the user to chat with.
        Create or get the private chat group and join it.
        '''

        self.user = self.scope["user"]
        self.other_user = self.scope["url_route"]["kwargs"]["username"]

        try:
          
            self.other_user_obj = await database_sync_to_async(User.objects.get)(username=self.other_user)

        except ObjectDoesNotExist:

            await self.accept()
            await self.send(text_data=json.dumps({
                "error": "User not found."
            }))
           
            await self.close(code=400)  # 4004 = Custom 'user not found' close code
            return
        

        self.group_name = get_private_group_name(self,self.user, self.other_user_obj)

        # Get or create ChatGroup
        self.chat_group = await self.get_or_create_chat_group(self.user, self.other_user_obj, self.group_name)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
      

    async def disconnect(self, close_code):
         
        # Leave the chat group when disconnected.
        if hasattr(self,"group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data =  json.loads(text_data)
        message = data["message"]

        # Save message to DB
        await self.save_message(self.chat_group, self.user, message)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": self.user.username
            }
        )

    async def chat_message(self, event):
            """
            Receive broadcast from group and forward to client,
                except to the sender themselves (avoid echo).
            """
            if self.user.username != event["sender"]:
                await self.send(text_data=json.dumps({
                        "message": event["message"],
                        "sender": event["sender"]
                    }))
                

    @database_sync_to_async
    def get_or_create_chat_group(self, user1, user2, group_name):
        # Get or create chat group in database
        return ChatGroup.objects.get_or_create(
            group_name=group_name,
            defaults={"sender": user1, "receiver": user2}
        )[0]

    @database_sync_to_async
    def save_message(self, group, sender, message):
        
        # save a chat to database
        return ChatMessages.objects.create(room=group, sender=sender, message=message)

   
