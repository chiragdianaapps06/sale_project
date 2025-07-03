import csv
from ..models import Item

def run():


    csv_file_path = 'C:\\Users\\Admin.DESKTOP-DVDNFOL.000\\Downloads\\5m Sales Records.csv'

    with open(csv_file_path,'r') as file:
        reader = csv.DictReader(file)

        next(reader)
        
        for row in reader:
            
            Item.objects.create(item_type = row['Item Type'], unit_cost=row['Unit Cost'])


            print("jjj====",row['Sales Channel'])


if __name__ == '__main__':
    run()