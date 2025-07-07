import csv
import os
import logging
from datetime import datetime

from ordering.models import Country, Order
from product.models import Item
from sale.models import Sales
from django.conf import settings
from django.db import transaction

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('data_import.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def run():
    csv_file_path = os.path.join(settings.BASE_DIR, 'data', '5m Sales Records.csv')

    batch_size = 5000
    try:
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)

           
           
            batch = []
            
            
            for row in reader:
                batch.append(row)
                
                
                if len(batch) >=batch_size:
                    batch_process(batch)
                  
                    batch = []
            

            if batch:
                batch_process(batch)
                

                    
                    
    except FileNotFoundError:
        logger.critical(f"CSV file not found at path: {csv_file_path}")
    except Exception as e:
        logger.critical(f"Fatal error occurred: {e}")






def batch_process(batch):
    
                
    orders_to_create = []
    sales_to_create = []
    item_to_create = []
    country_to_create = []

 
                    
    try:
        with transaction.atomic():



            for row in batch:
                item_exist = Item.objects.filter(
                    item_type=row['Item Type'].strip(),
                    unit_cost=float(row['Unit Cost']),
                ).first()
                print("item_exist",item_exist)
                

                if not item_exist:

                    item = Item(
                        item_type=row['Item Type'].strip(),
                        unit_cost=float(row['Unit Cost'])
                    )
                    item_to_create.append(item)
                
           

            
            Item.objects.bulk_create(item_to_create, batch_size=2000, ignore_conflicts=True)  
            logger.info(f" item inserted , batch size {len(item_to_create)}")
          
           
            for row in batch:
              
                country_exist = Country.objects.filter(
                    Country_name=row['Country'].strip(),
                    region=row['Region'].strip()
                ).first()
                if  not country_exist:
                    country = Country(
                        Country_name=row['Country'].strip(),
                        region=row['Region'].strip()
                    )

                    country_to_create.append(country)
                
            Country.objects.bulk_create(country_to_create, batch_size=2000, ignore_conflicts=True)
            logger.info(f" Country inserted , batch size {len(country_to_create)}")
            
            for row in batch:
                
                item_type = Item.objects.filter(   
                        item_type=row['Item Type'].strip(),
                        unit_cost=float(row['Unit Cost'])
                    ).first()
                
                country = Country.objects.filter(
                    Country_name=row['Country'].strip(),
                    region=row['Region'].strip()
                ).first()

                if not  item_type  or not country:
                    logger.warning(f"Skipping order due to missing item or country: {row['Order ID']}")
                    continue


                order = Order(
                    order_id=row['Order ID'].strip(),
                    item_type=item_type,
                    order_date=datetime.strptime(row['Order Date'], '%m/%d/%Y'),
                    ship_date=datetime.strptime(row['Ship Date'], '%m/%d/%Y'),
                    country= country,
                    order_priority=row['Order Priority'].strip(),
                    unit_sold=int(row['Units Sold']),
                    unit_price=float(row['Unit Price']),
                    total_price=float(row['Total Revenue']),
                )
                orders_to_create.append(order)
            
            Order.objects.bulk_create(orders_to_create ,batch_size=2000, ignore_conflicts=True)
            logger.info(f" Country inserted , batch size {len(orders_to_create)}")

            for row in batch:
                
                order_id = Order.objects.filter(order_id =  row['Order ID']).first()
                country = Country.objects.filter(
                        Country_name=row['Country'].strip(),
                        region=row['Region'].strip()
                    ).first()
                if not order or not country:
                    logger.warning(f"Skipping order due to missing order or country: {row['Order ID']}")
                    continue

                sale = Sales(
                    order_id=order_id,
                    sales_channel=row['Sales Channel'].strip(),
                    country=country,
                    unit_sold=int(row['Units Sold']),
                    total_cost=float(row['Total Cost']),
                    total_price=float(row['Total Revenue']),
                    total_revenue=float(row['Total Profit'])
                )

               
             
                sales_to_create.append(sale)

         
            
            Sales.objects.bulk_create(sales_to_create, batch_size=2000, ignore_conflicts=True)
            logger.info(f" sale data inserted , batch size {len(sales_to_create)}")

            

            
    except Exception as e:
        logger.warning(f"Batch failed: {e}")


if __name__ == '__main__':
    run()
