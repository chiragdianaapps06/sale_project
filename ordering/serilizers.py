from rest_framework import serializers
from .models import Order
import random
import string

class OrderSerializer(serializers.ModelSerializer):

    '''
       Serilaizer for order model
    '''

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_date', 'ship_date', 'order_id')

    def generate_unique_order_id(self):
        while True:
            order_id = int(''.join(random.choices(string.digits, k=10)))
            if not Order.objects.filter(order_id=order_id).exists():
                return order_id

    def create(self, validated_data):
        
        validated_data['order_id'] = self.generate_unique_order_id()
        return super().create(validated_data)