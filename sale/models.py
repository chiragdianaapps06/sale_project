from django.db import models
from ordering.models import Order,Country

# # Create your models here.
# Order_Id
# Sale_channel
# Region
# Country

SALE_CHANNEL_CHOICE =[
    ('online','online'),
    ('offline','offline')
]

# in my data order table has order_id 
class Sales(models.Model):
    order_id = models.OneToOneField(Order, on_delete=models.CASCADE)
    sales_channel = models.CharField(choices=SALE_CHANNEL_CHOICE)
    country = models.ForeignKey(Country,on_delete=models.CASCADE)
    unit_sold = models.IntegerField()
    total_cost = models.DecimalField(max_digits=10,decimal_places=2)
    total_price =  models.DecimalField(max_digits=10,decimal_places=2)
    total_revenue = models.DecimalField(max_digits=10,decimal_places=2)