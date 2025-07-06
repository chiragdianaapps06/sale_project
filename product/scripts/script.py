import csv
from ..models import Item

def run():


    csv_file_path = 'C:\\Users\\Admin.DESKTOP-DVDNFOL.000\\Downloads\\5m Sales Records.csv'

    with open(csv_file_path,'r') as file:
        reader = csv.DictReader(file)

        next(reader)
        i=0
        
        for row in reader:
            
            Item.objects.get_or_create(item_type = row['Item Type'], unit_cost=row['Unit Cost'])


            # print("jjj====",row['Sales Channel'])
            print("data saved",i)
            i+=1
           
           

if __name__ == '__main__':
    run()