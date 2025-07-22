from django.urls import path, include
from . import views

urlpatterns = [
    path('<str:username>/',views.ChatMessagesView.as_view(), name = "chat-message-view")
]
