from django.urls import path, include

# from rest_framework.routers import DefaultRouter
from .views import  OrderCreateApiView , OrderDetailAPIView

# routers = DefaultRouter()
# method={
#     'get':'list','post':'create'
# }
urlpatterns = [
    # path('orders/',OrderViewset.as_view(method),name='order-view'),
    path('',OrderCreateApiView.as_view(),name='order-view'), # exampple : orders/v2/
    
    # path('orders/v2/',OrderCreateApiView.as_view(),name='order-view'),
    path('<str:version>/',OrderCreateApiView.as_view(),name='order-view'), # exampple : v2/
    path('order/<int:pk>/',OrderDetailAPIView.as_view(),name='order-detail-view'),

   
    
]
