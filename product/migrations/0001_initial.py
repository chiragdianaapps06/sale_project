# Generated by Django 5.2.4 on 2025-07-11 08:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(max_length=100)),
                ('unit_cost', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ]
