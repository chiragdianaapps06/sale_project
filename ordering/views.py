from django.shortcuts import render
from rest_framework import viewsets, status
from .serilizers import OrderSerializer,OrderSerializerVersion2
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated,AllowAny , IsAdminUser

from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.versioning import URLPathVersioning



class OrderCreateApiView(APIView):
    
    """
    API View for creating and listing orders.
    Only authenticated users can access.
    """

    permission_classes = [IsAuthenticated]
    # versioning_class = URLPathVersioning

    def get_serializer_class(self):
        
        version = self.request.query_params.get('version', 'v1')
        if version == "v2":
            return OrderSerializerVersion2
        return OrderSerializer

    def get(self, request):
        
        queryset = Order.objects.all()



        # Filter non-superusers to see only their orders
        if not request.user.is_superuser:
            queryset = Order.objects.filter(agent = request.user)

        # Filter the Country
        country = request.GET.get('country')
        if country:
            queryset = queryset.filter(country=country)


        ordering = request.GET.get("ordering")
        if ordering:
            queryset = queryset.order_by(ordering)

        serializer_class = self.get_serializer_class()

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = serializer_class(paginated_qs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):

        """
        Create a new order. Automatically assigns:
        - `order_id`
        - `agent` based on user or input
        """
        try:
            print("login user: ", request.user)
            # serializer = OrderSerializer(data=request.data,context={'request':request})
            serializer_class = self.get_serializer_class()
            serializer = serializer_class(data=request.data,context={'request':request})
        
            if serializer.is_valid():
                serializer.save()
                resp =Response(serializer.data,status=status.HTTP_201_CREATED)
                resp.message = "order save successfully."
                return resp
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
              return Response(
                    {"error": "An unexpected error occurred.", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class OrderDetailAPIView(APIView):
    '''
    API View for handling a specific order.
    Supports:
    - Retrieve (GET)
    - Update (PUT/PATCH)
    - Soft delete (DELETE)
    
    '''
    
    def get_object(self, pk):

        
        # Fetch a specific Order object by primary key.
        
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        #  Retrieve an order by ID.
        order = self.get_object(pk)
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
       
        serializer = OrderSerializer(order)
        response =  Response(serializer.data, status=status.HTTP_200_OK)
        response.message = "Order data found."
        return response

    def put(self, request, pk):

        # Full update of an order.
        order = self.get_object(pk)
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
       
        serializer =  OrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, pk):
        # Partial update of an order.
        order = self.get_object(pk)
        if not order:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        # Soft delete an order (sets is_deleted = True).

        try:
            order = self.get_object(pk)
            if not order:
                return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
            order.is_deleted = True
            order.save()
            return Response({"message": "Order soft-deleted."}, status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            return Response({"error": "Failed to delete order.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


