import csv
from ..models import Country,Order
from product.models import Item

def run():

    
    # csv_file_path = 'C:\\Users\\Admin.DESKTOP-DVDNFOL.000\\Downloads\\5m Sales Records.csv'


    
    # with open(csv_file_path,'r') as file:
    #     reader = csv.DictReader(file)

    #     # next(reader)
    #     i=0
    #     # itemtype = Item.object.filt(item_type=)
    #     for row in reader:
    #         # itemtype = Item.objects.filter(item_type=row['Item Type']).first()
    #         # for item in itemtype:
    #         #     item_id = item.id

    #         # country = Country.objects.filter( Country_name = row['Country']).first()
    #         # print("----",country)

    #         # for item in country:
    #         #     print(item.id)
    #         # print("error----",row['C'])
    #         # print("error====",row['Order ID'])
    #         # break
           
            

    #         # Order.objects.get_or_create(order_id = row['Order ID'],item_type =itemtype,order_date = row['Order Date'],ship_date=row['Ship Date'],country =country, order_priority = row['Order Priority'],unit_sold = row['Units Sold'],unit_price = row['Unit Price'], total_price = row['Total Revenue']) 
    #         # print(itemtype)
            
    #         print("data pass",i)
    #         i+=1

    print(111)
        
            






if __name__ == '__main__':
    run()