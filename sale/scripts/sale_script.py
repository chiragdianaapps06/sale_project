import csv
from ..models import Sales
from ordering.models import Country , Order

def run():

    
    csv_file_path = 'C:\\Users\\Admin.DESKTOP-DVDNFOL.000\\Downloads\\5m Sales Records.csv'


    
    with open(csv_file_path,'r') as file:
        reader = csv.DictReader(file)

        # next(reader)
        i=0
        
        for row in reader:
            
            order_id = Order.objects.get(pk=row['Order ID'])
            print("order===",order_id)
            break

            country = Country.objects.filter(Country_name = row['Country']).first()
            print("----",country)

           
            
        
            Sales.objects.get_or_create(order = order_id , sales_channel= row['Sales Channel'],country=country,unit_sold= row['Units Sold'],total_cost=row['Total Cost'],total_price=row['Total Revenue'],total_revenue =  row['Total Profit']) 
            # print(itemtype)
            
            print("data pass",i)
            i+=1
        
            






if __name__ == '__main__':
    run()