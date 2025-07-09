import csv
import os
import logging
from datetime import datetime
from django.db import transaction
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, as_completed 
import threading
import gc

from ordering.models import Country, Order
from product.models import Item
from sale.models import Sales

# Setup logging
FILE_NAME = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
logs_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, FILE_NAME)

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

            existing_countries = {
                (country.Country_name.strip(), country.region.strip()): country
                for country in Country.objects.all()
            }

            existing_items = {
                (item.item_type.strip(), float(item.unit_cost)): item
                for item in Item.objects.all()
            }
            existing_orders = {
                o.order_id: o for o in Order.objects.all()
            }
            


            for row in reader:
                batch.append(row)
                if len(batch) >= batch_size:

                    batch_process(batch,existing_countries,existing_items,existing_orders )
                    logger.info(f"Processed batch up to row {count + batch_size}")
                     
                       
                    count += batch_size
                    batch = []

            if batch:
                batch_process(batch,existing_countries,existing_items,existing_orders)
               
                logger.info(f"Processed final batch up to row {count + len(batch)}")

            
          

    except FileNotFoundError:
        logger.critical(f"CSV file not found at path: {csv_file_path}")
    except Exception as e:
        logger.critical(f"Fatal error occurred: {e}")


def product_items_process(batch,existing_items,items_to_create):
    new_item_keys = set()
    logger.info(f"[{threading.current_thread().name}] Running item_process on batch of size {len(batch)}")

    for row in batch:
        try:
            item_key = (row['Item Type'].strip(), float(row['Unit Cost']))
            if item_key not in existing_items and item_key not in new_item_keys:
                item = Item(item_type=item_key[0], unit_cost=item_key[1])
                items_to_create.append(item)
                new_item_keys.add(item_key)
        except Exception as e:
            logger.warning(f"Item skip: {e}")
            continue
    logger.info(f"[{threading.current_thread().name}] item created in current batch {len(items_to_create)}")

def country_process(batch,existing_countries,countries_to_create):
    new_country_keys = set()

    logger.info(f"[{threading.current_thread().name}] Running country_process on batch of size {len(batch)}")
    for row in batch:
        try:
            country_key = (row['Country'].strip(), row['Region'].strip())
            if country_key not in existing_countries and country_key not in new_country_keys:
                country = Country(Country_name=country_key[0], region=country_key[1])
                countries_to_create.append(country)
                new_country_keys.add(country_key)
        except Exception as e:
            logger.warning(f"Country skip: {e}")
            continue
    logger.info(f"[{threading.current_thread().name}] cuntries created in current bacth {len(countries_to_create)}")


def order_process(batch,existing_items,existing_countries,existing_orders,orders_to_create):

    logger.info(f"[{threading.current_thread().name}] Running order_process on batch of size {len(batch)}")

    new_order_keys = set()
    for row in batch:
        try:
            item_key = (row['Item Type'].strip(), float(row['Unit Cost']))
            country_key = (row['Country'].strip(), row['Region'].strip())
            item = existing_items.get(item_key)
            country = existing_countries.get(country_key)
            if not item or not country:
                continue
            order_id = row['Order ID'].strip()
          

            if str(order_id) not in  existing_orders:
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
            logger.warning(f"Order skip: {e}")
            continue
    logger.info(f"[{threading.current_thread().name}] order created in current batch {len(orders_to_create)}")


    

def sale_process(batch,existing_orders,existing_countries,sales_to_create):


    
    order_ids = [r['Order ID'].strip() for r in batch ]

    
    existing_orders.update({
        o.order_id: o
        for o in Order.objects.filter(order_id__in=order_ids)
        
    })



    logger.info(f"[{threading.current_thread().name}] Running sales process on batch of size {len(batch)}")
    for row in batch:
        try:
       
            order = existing_orders.get(int(row['Order ID'].strip()))
            country = existing_countries.get((row['Country'].strip(), row['Region'].strip()))
   
            if not order or not country:
                continue
           
            sale = Sales(
                order_id=order,
                sales_channel=row['Sales Channel'].strip(),
                country=country,
                unit_sold=int(row['Units Sold']),
                total_cost=float(row['Total Cost']),
                total_price=float(row['Total Revenue']),
                total_revenue=float(row['Total Profit']),
            )
            sales_to_create.append(sale)
        except Exception as e:
            logger.warning(f"Sale skip: {e}")
            continue
    logger.info(f"[{threading.current_thread().name}] sales created in current bacth {len(sales_to_create)}")



def batch_process(batch,existing_items, existing_countries,existing_orders):
  

    orders_to_create = []
    sales_to_create = []
    items_to_create = []
    countries_to_create = []

    try:
        with transaction.atomic():
           

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                futures.append(executor.submit(product_items_process,batch,existing_items,items_to_create))
                for future in futures:
                    future.result()

            Item.objects.bulk_create(items_to_create, batch_size=2000, ignore_conflicts=True)

            existing_items.update({
                (item.item_type.strip(), float(item.unit_cost)): item
                for item in Item.objects.filter(item_type__in=[r['Item Type'].strip() for r in batch])
            })

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures =[]
                futures.append(executor.submit(country_process,batch,existing_countries,countries_to_create))

                for future in futures:
                    future.result()
            Country.objects.bulk_create(countries_to_create, batch_size=2000, ignore_conflicts=True)


            existing_countries.update({
                (c.Country_name.strip(), c.region.strip()): c
                for c in Country.objects.filter(Country_name__in=[r['Country'].strip() for r in batch])
            })

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures =[]
                futures.append(executor.submit(order_process,batch,existing_items,existing_countries,existing_orders,orders_to_create))

                for future in futures:
                    future.result()

            Order.objects.bulk_create(orders_to_create, batch_size=2000, ignore_conflicts=True)


            order_ids = [r['Order ID'].strip() for r in batch ]

            
            existing_orders.update({
                o.order_id: o
                for o in Order.objects.filter(order_id__in=order_ids)
                
            })

            

            

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures =[]
                futures.append(executor.submit(sale_process,batch,existing_orders,existing_countries,sales_to_create))

                for future in futures:
                    future.result()
           

            Sales.objects.bulk_create(sales_to_create, batch_size=2000, ignore_conflicts=True)



            # Clear memory
            batch.clear()
            items_to_create.clear()
            countries_to_create.clear()
            orders_to_create.clear()
            sales_to_create.clear()
            gc.collect()

    except Exception as e:
        logger.warning(f"Batch failed: {e} ")


if __name__ == '__main__':
    run()


