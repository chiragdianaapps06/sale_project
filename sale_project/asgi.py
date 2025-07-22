"""
ASGI config for sale_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sale_project.settings')

django_asgi_app = get_asgi_application()

from chatapp.routing import websocket_urlpatterns
from chatapp.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket":
        JWTAuthMiddleware(                     
            URLRouter(websocket_urlpatterns)
        )
    
})


# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket":
#         SessionMiddlewareStack(
#             AuthMiddlewareStack(
#                 URLRouter(
#                     websocket_urlpatterns
#                 )
#             )
#         )
#     ,
# })