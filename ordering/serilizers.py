from rest_framework import serializers
from .models import Order
import random
import string
from django.contrib.auth import get_user_model

User = get_user_model()

class OrderSerializer(serializers.ModelSerializer):

    '''
       Serilaizer for order model
    '''

    # agent = serializers.HyperlinkedRelatedField(view_name='user-detail', queryset=User.objects.all())

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('order_date', 'ship_date', 'order_id')

    def generate_unique_order_id(self):

        """
        Generates a unique 10-digit numeric order ID.
        Ensures uniqueness by checking against the database.
        """
        while True:
            order_id = int(''.join(random.choices(string.digits, k=10)))
            if not Order.objects.filter(order_id=order_id).exists():
                return order_id
            
   


    def create(self, validated_data):

        """
        Custom create method:
        - Sets the agent as per user role.
        - Validates superuser must specify agent.
        - Generates a unique order ID.
        """

        
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            
            # Superusers must provide an agent ID
            if request.user.is_superuser :
                agent_id = request.data.get('agent')
                if agent_id:
                    try:
                        validated_data['agent'] = User.objects.get(id = agent_id)
                
                    except User.DoesNotExist:
                        raise serializers.ValidationError({"agent": "Invalid agent ID"})
                    
                else:
                    raise serializers.ValidationError({"agent": "Superuser must specify agent"})

            # Non-superusers are automatically assigned as agent 
            else:
                validated_data['agent'] = request.user 
       
        

            # Add generated unique order ID
        validated_data['order_id'] = self.generate_unique_order_id()
        return super().create(validated_data)


class OrderSerializerVersion2(serializers.ModelSerializer):

    '''
       Serilaizer for order model
    '''

   
    class Meta:
        model = Order
        fields  = ['order_id','agent','order_priority','country','unit_sold','unit_price','total_price','item_type']
        read_only_fields = ('order_date', 'ship_date', 'order_id')

    def generate_unique_order_id(self):

        """
        Generates a unique 10-digit numeric order ID.
        Ensures uniqueness by checking against the database.
        """
        while True:
            order_id = int(''.join(random.choices(string.digits, k=10)))
            if not Order.objects.filter(order_id=order_id).exists():
                return order_id

    def create(self, validated_data):

        """
        Custom create method:
        - Sets the agent as per user role.
        - Validates superuser must specify agent.
        - Generates a unique order ID.
        """

        
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            
            # Superusers must provide an agent ID
            if request.user.is_superuser :
                agent_id = request.data.get('agent')
                if agent_id:
                    try:
                        validated_data['agent'] = User.objects.get(id = agent_id)
                
                    except User.DoesNotExist:
                        raise serializers.ValidationError({"agent": "Invalid agent ID"})
                    
                else:
                    raise serializers.ValidationError({"agent": "Superuser must specify agent"})

            # Non-superusers are automatically assigned as agent 
            else:
                validated_data['agent'] = request.user 
       
        

            # Add generated unique order ID
        validated_data['order_id'] = self.generate_unique_order_id()
        return super().create(validated_data)
    
    def to_representation(self, instance):
        """
        Customize the fields returned for GET requests.
        Returns fewer fields for GET requests than for POST.
        """
        request = self.context.get('request')

        if request and request.method == 'GET':
            # For GET requests, only return selected fields (e.g., 'order_id', 'order_priority', 'unit_sold', etc.)
            return {
                'order_id': instance.order_id,
                'order_priority': instance.order_priority,
                'unit_sold': instance.unit_sold,
                'total_price': instance.total_price,
                # Add more fields as necessary for GET
            }
        
        # Default case for POST or other methods, return all fields
        return super().to_representation(instance)
    


# class OrderHyperlinkSerializer(serializers.HyperlinkedModelSerializer):

#     '''
#        Serilaizer for order model
#     '''

#     class Meta:
#         model = Order
#         fields = '__all__'
#         read_only_fields = ('order_date', 'ship_date', 'order_id')

#     def generate_unique_order_id(self):

#         """
#         Generates a unique 10-digit numeric order ID.
#         Ensures uniqueness by checking against the database.
#         """
#         while True:
#             order_id = int(''.join(random.choices(string.digits, k=10)))
#             if not Order.objects.filter(order_id=order_id).exists():
#                 return order_id

#     def create(self, validated_data):

#         """
#         Custom create method:
#         - Sets the agent as per user role.
#         - Validates superuser must specify agent.
#         - Generates a unique order ID.
#         """

        
#         request = self.context.get('request')
        
#         if request and hasattr(request, 'user'):
            
#             # Superusers must provide an agent ID
#             if request.user.is_superuser :
#                 agent_id = request.data.get('agent')
#                 if agent_id:
#                     try:
#                         validated_data['agent'] = User.objects.get(id = agent_id)
                
#                     except User.DoesNotExist:
#                         raise serializers.ValidationError({"agent": "Invalid agent ID"})
                    
#                 else:
#                     raise serializers.ValidationError({"agent": "Superuser must specify agent"})

#             # Non-superusers are automatically assigned as agent 
#             else:
#                 validated_data['agent'] = request.user 
       
        

#             # Add generated unique order ID
#         validated_data['order_id'] = self.generate_unique_order_id()
#         return super().create(validated_data)