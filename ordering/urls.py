from django.urls import path, include

# from rest_framework.routers import DefaultRouter
from .views import  OrderCreateApiView

# routers = DefaultRouter()
# method={
#     'get':'list','post':'create'
# }
urlpatterns = [
    # path('orders/',OrderViewset.as_view(method),name='order-view'),
    path('orders/',OrderCreateApiView.as_view(),name='order-view'),
    
]
