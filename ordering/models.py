from django.db import models

from product.models import Item

class Country(models.Model):
    Country_name = models.CharField()
    region =  models.CharField()


# class Order(models.Model):
#     order_id = models.PositiveIntegerField(primary_key=True)
#     item_type = models.ForeignKey(Item,on_delete=models.CASCADE)
#     order_date =  models.DateField(auto_now=True)
#     ship_date = models.DateField(auto_now=True)
#     country = models.ForeignKey(Country,on_delete=models.CASCADE)
#     order_priority = models.CharField(choices=)

    