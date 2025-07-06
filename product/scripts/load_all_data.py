import csv
import os
import logging
from datetime import datetime

from ordering.models import Country, Order
from product.models import Item
from sale.models import Sales 
from django.conf import settings

# Setup logging
logging.basicConfig(
    filename='data_import.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Setup logging to both file and console
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('data_import.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def run():
    csv_file_path = os.path.join(settings.BASE_DIR, 'data', '5m Sales Records.csv')

    try:
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            i = 0

            for row in reader:
                try:
                  
                    try:
                        item, _ = Item.objects.get_or_create(
                            item_type=row['Item Type'].strip(),
                            unit_cost=float(row['Unit Cost'])
                        )
                       
                    except Exception as e:
                        logging.warning(f"Row {i} skipped - Failed to fetch/create Item: {e}")
                        continue

                
                    try:
                        country, _ = Country.objects.get_or_create(
                            Country_name=row['Country'].strip(),
                            region=row['Region'].strip()
                        )
                    except Exception as e:
                        logging.warning(f"Row {i} skipped - Failed to fetch/create Country: {e}")
                        continue

                    try:
                        order, _ = Order.objects.get_or_create(
                            order_id=row['Order ID'].strip(),
                            # defaults={
                            #     'item_type': item,
                            #     'order_date': datetime.strptime(row['Order Date'], '%m/%d/%Y'),
                            #     'ship_date': datetime.strptime(row['Ship Date'], '%m/%d/%Y'),
                            #     'country': country,
                            #     'order_priority': row['Order Priority'].strip(),
                            #     'unit_sold': int(row['Units Sold']),
                            #     'unit_price': float(row['Unit Price']),
                            #     'total_price': float(row['Total Revenue']),
                            # }
                            item_type = item,
                            order_date  = datetime.strptime(row['Order Date'], '%m/%d/%Y'),
                            ship_date  = datetime.strptime(row['Ship Date'], '%m/%d/%Y'),
                            country  = country,
                            order_priority = row['Order Priority'].strip(),
                            unit_sold  = int(row['Units Sold']),
                            unit_price = float(row['Unit Price']),
                            total_price  = float(row['Total Revenue']),
                        )
                    except Exception as e:
                        logging.warning(f"Row {i} skipped - Failed to create Order: {e}")
                        continue

                  
                    try:
                        order_id = Order.objects.get(pk=row['Order ID'])
                        Sales.objects.get_or_create(
                            order_id=order_id,
                            sales_channel=row['Sales Channel'].strip(),
                            country=country,
                            unit_sold=int(row['Units Sold']),
                            total_cost=float(row['Total Cost']),
                            total_price=float(row['Total Revenue']),
                            total_revenue=float(row['Total Profit'])
                        )
                    except Exception as e:
                        logging.warning(f"Row {i} skipped - Failed to create Sales: {e}")
                        continue

                    logging.info(f"Row {i} successfully imported. Order ID: {row['Order ID']}")
                    i += 1

                    if i==5:
                        break

                except Exception as e:
                    logging.error(f"Row {i} - General error: {e}")
                    continue

    except FileNotFoundError:
        logging.critical(f"CSV file not found at path: {csv_file_path}")
    except Exception as e:
        logging.critical(f"Fatal error occurred: {e}")






if __name__ == '__main__':
    run()