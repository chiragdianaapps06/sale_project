import csv
import os
import logging
from datetime import datetime
from collections import defaultdict
from django.db import transaction , connection
from django.db import close_old_connections

from ordering.models import Country, Order
from product.models import Item
from sale.models import Sales
from django.conf import settings




# Setup logging
FILE_PATH = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
logs_path = os.path.join(os.getcwd(),'logs',FILE_PATH)
os.makedirs(logs_path,exist_ok=True)
log_file_path = os.path.join(logs_path,FILE_PATH)
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())  





def run():
    csv_file_path = os.path.join(settings.BASE_DIR, 'data', '5m Sales Records.csv')
    batch_size = 10000
    batch = []
    count = 0
   

       
    try:
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)

            for row in reader:
                batch.append(row)
                if len(batch) >= batch_size:

                    batch_process(batch)
                    logger.info(f"Processed batch up to row {count + batch_size}")
                     
                       
                    count += batch_size
                    batch = []

            if batch:
                batch_process(batch)
               
                logger.info(f"Processed final batch up to row {count + len(batch)}")

            
          

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

          
            existing_countries = {
                (country.Country_name.strip(), country.region.strip()): country
                for country in Country.objects.all()
            }

            existing_items = {
                (item.item_type.strip(), float(item.unit_cost)): item
                for item in Item.objects.all()
            }

            new_item_keys = set()
            new_country_keys = set()

            


            for row in batch:

                try:
                    item_key = (row['Item Type'].strip(), float(row['Unit Cost']))
                    if item_key not in existing_items and item_key not in new_item_keys:
                        item = Item(item_type=item_key[0], unit_cost=item_key[1])
                        item_to_create.append(item)
                        new_item_keys.add(item_key)
                
                except Exception as e:
                    logger.warning(f"Skipping item creation for row due to error: {e}")
                    continue


            Item.objects.bulk_create(item_to_create, batch_size=2000, ignore_conflicts=True)

            
            for row in batch:
                try:

                    country_key = (row['Country'].strip(), row['Region'].strip())
                    if country_key not in existing_countries and country_key not in new_country_keys:
                        country = Country(Country_name=country_key[0], region=country_key[1])
                        country_to_create.append(country)
                        new_country_keys.add(country_key)
                except Exception as e:
                    logger.warning(f"Skipping country creation for row due to error: {e}")
                    continue


            Country.objects.bulk_create(country_to_create, batch_size=2000, ignore_conflicts=True)

            existing_items.update({
                (item.item_type.strip(), float(item.unit_cost)): item
                for item in Item.objects.filter(item_type__in=[r['Item Type'].strip() for r in batch])
            })
            existing_countries.update({
                (country.Country_name.strip(), country.region.strip()): country
                for country in Country.objects.filter(Country_name__in=[r['Country'].strip() for r in batch])
            })


            for row in batch:

                try:

                    item_key = (row['Item Type'].strip(), float(row['Unit Cost']))
                    country_key = (row['Country'].strip(), row['Region'].strip())

                    item = existing_items.get(item_key)
                    country = existing_countries.get(country_key)

                    if not item or not country:
                        logger.warning(f"Skipping order due to missing item or country: {row['Order ID']}")
                        continue

                    order = Order(
                        order_id=row['Order ID'].strip(),
                        item_type=item,
                        order_date=datetime.strptime(row['Order Date'], '%m/%d/%Y'),
                        ship_date=datetime.strptime(row['Ship Date'], '%m/%d/%Y'),
                        country=country,
                        order_priority=row['Order Priority'].strip(),
                        unit_sold=int(row['Units Sold']),
                        unit_price=float(row['Unit Price']),
                        total_price=float(row['Total Revenue']),
                    )
                    orders_to_create.append(order)


                except Exception as e:
                    logger.warning(f"Skipping order creation due to error : {e}")
                    continue



            Order.objects.bulk_create(orders_to_create, batch_size=2000, ignore_conflicts=True)

            # # Step 4: Create Sales

            order_ids = [r['Order ID'].strip() for r in batch ]

            
            existing_orders = {
                o.order_id: o
                for o in Order.objects.filter(order_id__in=order_ids)
                
            }
            
            
            for row in batch:
                try:


                    order = existing_orders.get(int(row['Order ID'].strip()))
                   
                    country = existing_countries.get((row['Country'].strip(), row['Region'].strip()))
       

                    if not order or not country:
                        logger.warning(f"Skipping sale due to missing order or country: {row['Order ID']}")
                        continue

                    sale = Sales(
                        order_id=order,
                        sales_channel=row['Sales Channel'].strip(),
                        country=country,
                        unit_sold=int(row['Units Sold']),
                        total_cost=float(row['Total Cost']),
                        total_price=float(row['Total Revenue']),
                        total_revenue=float(row['Total Profit'])
                    )
                    sales_to_create.append(sale)

                except Exception as e:
                    logger.warning(f"Skipping sale creations due to error : {e}")
                    continue


            
            Sales.objects.bulk_create(sales_to_create, batch_size=2000, ignore_conflicts=True)
            logger.info(f"Inserted: {len(item_to_create)} Items, {len(country_to_create)} Countries, {len(orders_to_create)} Orders, {len(sales_to_create)} Sales")
            
           


    except Exception as e:
        logger.warning(f"Batch failed: {e} ")
      
        
    



if __name__ == '__main__':
    run()

