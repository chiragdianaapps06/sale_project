from django.db import models

from product.models import Item
from.choice import ORDER_PRIORITY_CHOICES

class Country(models.Model):
    Country_name = models.CharField()
    region =  models.CharField()
 



class Order(models.Model):
    order_id = models.BigIntegerField(primary_key=True)
    item_type = models.ForeignKey(Item,on_delete=models.CASCADE ,related_name='product_item', default=None)
    order_date =  models.DateField(auto_now=True)
    ship_date = models.DateField(auto_now=True)
    country = models.ForeignKey(Country,on_delete=models.CASCADE)
    order_priority = models.CharField(choices=ORDER_PRIORITY_CHOICES)
    unit_sold = models.IntegerField()
    unit_price =  models.DecimalField(max_digits=10,decimal_places=2)
    total_price =  models.DecimalField(max_digits=10,decimal_places=2)

    