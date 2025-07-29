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
from rest_framework.decorators import action


class OrderCreateApiView(APIView):
    
    """
    API View for creating and listing orders.
    Only authenticated users can access.
    """

    permission_classes = [IsAuthenticated]
    # versioning_class = URLPathVersioning

    def get_serializer_class(self,version):
        print("++",type(version))
        
        # version = self.request.query_params.get('version', 'v1')
        if version == "v2":
            return OrderSerializerVersion2
        return OrderSerializer

    def get(self, request,version=None):
        
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

        agent = request.GET.get('agent')
        if agent:
            queryset = queryset.filter(agent__id=agent)

        order_priority = request.GET.get('order_priority')
        if order_priority:
            queryset = queryset.filter(order_priority=order_priority)


        serializer_class = self.get_serializer_class(version)

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = serializer_class(paginated_qs, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self,request, version = None):

        if isinstance(request.data,list):
            return    self.bulk_create(request,version)

        return self.single_create(request, version)

    def single_create(self, request, version = None):

        """
        Create a new order. Automatically assigns:
        - `order_id`
        - `agent` based on user or input
        """
        try:
            print("login user: ", request.user)
            # serializer = OrderSerializer(data=request.data,context={'request':request})
            serializer_class = self.get_serializer_class(version)
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
        
    
    def bulk_create(self, request, version):
        """
        Bulk create multiple orders in a single API request.
        """
        try:
            data = request.data
            orders = []
            
            for order_data in data:
                serializer_class = self.get_serializer_class(version)
                serializer = serializer_class(data=order_data,context={'request':request})
                if serializer.is_valid():
                    order = serializer.save()
                    orders.append(order)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Serialize the created orders to return
            created_orders = OrderSerializer(orders, many=True)
            return Response(created_orders.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": "An unexpected error occurred.", "details": str(e)},
                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def put(self, request, *args, **kwargs):
            """
            Bulk update multiple orders.
            """
            data = request.data  # List of orders to be updated
            updated_orders = []  # List to store successfully updated orders
            failed_orders = []  # List to store orders that failed to update


            for order_data in data:
                try:
                    # Get the order object based on order_id
                    order = Order.objects.get(order_id=order_data['order_id'])
        

                    # Serialize the data for each order separately
                    serializer = OrderSerializer(order, data=order_data, partial = True)  # partial=True allows partial updates

                    # print("====",serializer)
                    if serializer.is_valid():
                   
                        serializer.save()
                        updated_orders.append(serializer.data)  # Store the successfully updated order
                    else:
                        failed_orders.append({
                            "order_id": order_data['order_id'],
                            "errors": serializer.errors
                        })
                except Order.DoesNotExist:
                    failed_orders.append({
                        "order_id": order_data['order_id'],
                        "errors": "Order not found."
                    })

            # Prepare the response data
            response_data = {
                "status": "success" if updated_orders else "failure",
                "updated_orders": updated_orders,
                "failed_orders": failed_orders
            }

            return Response(response_data, status=status.HTTP_200_OK)

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
        print("order id",pk)
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


