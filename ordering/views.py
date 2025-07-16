from django.shortcuts import render
from rest_framework import viewsets, status
from .serilizers import OrderSerializer
from rest_framework.views import APIView
from rest_framework.response import Response



class OrderCreateApiView(APIView):

    '''APiview for order creation'''


    def post(self, request):

        """Create an order"""
        try:

            serializer = OrderSerializer(data=request.data)
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
