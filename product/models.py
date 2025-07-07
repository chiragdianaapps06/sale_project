from django.db import models

# Create your models here.


class Item(models.Model):

    item_type = models.CharField(max_length=100)
    unit_cost =  models.DecimalField(max_digits=10,decimal_places=2)

    # def __str__(self):
    #     return self.id