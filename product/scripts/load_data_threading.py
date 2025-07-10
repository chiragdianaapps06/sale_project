
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


def batch_generator(reader, batch_size=10000):
    batch = []
    for row in reader:
        batch.append(row)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def run():
    csv_file_path = os.path.join(settings.BASE_DIR, 'data', '5m Sales Records.csv')
    batch_size = 10000

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

            c=0
            for count, batch in enumerate(batch_generator(reader, batch_size)):
                batch_process(batch, existing_items, existing_countries, existing_orders)
                # logger.info(f"Processed batch {count + 1}")

                logger.info(f"Processed batch up to row {c+ batch_size}")
                
                c+=batch_size
                       
#                     count += batch_size

    except FileNotFoundError:
        logger.critical(f"CSV file not found at path: {csv_file_path}")
    except Exception as e:
        logger.critical(f"Fatal error occurred: {e}")


def product_items_process(batch, existing_items, items_to_create):
    new_item_keys = set()
    for row in batch:
        try:
            item_key = (row['Item Type'].strip(), float(row['Unit Cost']))
            if item_key not in existing_items and item_key not in new_item_keys:
                items_to_create.append(Item(item_type=item_key[0], unit_cost=item_key[1]))
                new_item_keys.add(item_key)
        except Exception as e:
            logger.warning(f"Item skip: {e}")
    logger.info(f"[{threading.current_thread().name}] Items to create: {len(items_to_create)}")


def country_process(batch, existing_countries, countries_to_create):
    new_country_keys = set()
    for row in batch:
        try:
            country_key = (row['Country'].strip(), row['Region'].strip())
            if country_key not in existing_countries and country_key not in new_country_keys:
                countries_to_create.append(Country(Country_name=country_key[0], region=country_key[1]))
                new_country_keys.add(country_key)
        except Exception as e:
            logger.warning(f"Country skip: {e}")
    logger.info(f"[{threading.current_thread().name}] Countries to create: {len(countries_to_create)}")


def order_process(batch, existing_items, existing_countries, existing_orders, orders_to_create):
    for row in batch:
        try:
            item_key = (row['Item Type'].strip(), float(row['Unit Cost']))
            country_key = (row['Country'].strip(), row['Region'].strip())
            order_id = row['Order ID'].strip()

            item = existing_items.get(item_key)
            country = existing_countries.get(country_key)

            if not item or not country or order_id in existing_orders:
                continue

            orders_to_create.append(Order(
                order_id=order_id,
                item_type=item,
                order_date=datetime.strptime(row['Order Date'], '%m/%d/%Y'),
                ship_date=datetime.strptime(row['Ship Date'], '%m/%d/%Y'),
                country=country,
                order_priority=row['Order Priority'].strip(),
                unit_sold=int(row['Units Sold']),
                unit_price=float(row['Unit Price']),
                total_price=float(row['Total Revenue']),
            ))
        except Exception as e:
            logger.warning(f"Order skip: {e}")
    logger.info(f"[{threading.current_thread().name}] Orders to create: {len(orders_to_create)}")


def sale_process(batch, existing_orders, existing_countries, sales_to_create):


    for row in batch:
        try:
            order = existing_orders.get(int(row['Order ID'].strip()))
            country_key = (row['Country'].strip(), row['Region'].strip())
            country = existing_countries.get(country_key)

        
            if not order or not country:
                continue

           
            

            sales_to_create.append(Sales(
                order_id=order,
                sales_channel=row['Sales Channel'].strip(),
                country=country,
                unit_sold=int(row['Units Sold']),
                total_cost=float(row['Total Cost']),
                total_price=float(row['Total Revenue']),
                total_revenue=float(row['Total Profit']),
            ))
            
        except Exception as e:
            logger.warning(f"Sale skip: {e}")
    logger.info(f"[{threading.current_thread().name}] Sales to create: {len(sales_to_create)}")


def batch_process(batch, existing_items, existing_countries, existing_orders):
    items_to_create = []
    countries_to_create = []
    orders_to_create = []
    sales_to_create = []

    try:
        with transaction.atomic():
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(product_items_process, batch, existing_items, items_to_create),
                    executor.submit(country_process, batch, existing_countries, countries_to_create),
                    executor.submit(order_process, batch, existing_items, existing_countries, existing_orders, orders_to_create),
                ]
                for future in as_completed(futures):
                    future.result()

            Item.objects.bulk_create(items_to_create, batch_size=2000, ignore_conflicts=True)
            Country.objects.bulk_create(countries_to_create, batch_size=2000, ignore_conflicts=True)
            Order.objects.bulk_create(orders_to_create, batch_size=2000, ignore_conflicts=True)
            
            Sales.objects.bulk_create(sales_to_create, batch_size=2000, ignore_conflicts=True)

            existing_items.update({
                (item.item_type.strip(), float(item.unit_cost)): item
                for item in Item.objects.filter(item_type__in=[r['Item Type'].strip() for r in batch])
            })

            existing_countries.update({
                (c.Country_name.strip(), c.region.strip()): c
                for c in Country.objects.filter(Country_name__in=[r['Country'].strip() for r in batch])
            })

            existing_orders.update({
                o.order_id: o for o in Order.objects.filter(order_id__in=[r['Order ID'].strip() for r in batch])
            })

            with ThreadPoolExecutor(max_workers=2) as executor:
              futures = [
                  executor.submit(sale_process,batch, existing_orders, existing_countries, sales_to_create)
              ]
              for future in futures:
                  future.result()



            # sale_process(batch, existing_orders, existing_countries, sales_to_create)
            Sales.objects.bulk_create(sales_to_create, batch_size=2000, ignore_conflicts=True)


            # Clear memory
            batch.clear()
            items_to_create.clear()
            countries_to_create.clear()
            orders_to_create.clear()
            sales_to_create.clear()
            gc.collect()

    except Exception as e:
        logger.warning(f"Batch failed: {e}")


if __name__ == '__main__':
    run()

