import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework import status

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        token = None

        # Get token from cookies
        if b"cookie" in headers:
            cookies = headers[b"cookie"].decode()
            cookie_dict = {
                c.split("=")[0].strip(): c.split("=")[1].strip()
                for c in cookies.split(";") if "=" in c
            }
            token = cookie_dict.get("token")

        if not token:
            await self._reject_connection(send)
            return

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = await self.get_user(payload.get("user_id"))
            if user is None:
                raise Exception("User not found")
            scope["user"] = user
        except Exception:
            scope["user"] = AnonymousUser()
            await self._reject_connection(send)
            return

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    async def _reject_connection(self, send):
        """
        Reject unauthorized WebSocket connections
        """
        await send({
            "type": "websocket.close",
            "status": status.HTTP_401_UNAUTHORIZED  # Custom close code for unauthorized
        })
