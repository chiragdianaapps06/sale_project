import csv
from product.models import Item

def run():


    csv_file_path = 'C:\Users\Admin.DESKTOP-DVDNFOL.000\Downloads\5m Sales Records.csv'

    with open(csv_file_path,'r') as file:
        reader = csv.reader(file)

        # next(reader)

        for row in reader:
            Item.objects.create(item_type = row['Item Type'], unit_cost=['Unit Cost'])


if __name__ == '__main__':
    run()