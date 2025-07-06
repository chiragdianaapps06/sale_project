import csv
from ..models import Country

def run():

    
    csv_file_path = 'C:\\Users\\Admin.DESKTOP-DVDNFOL.000\\Downloads\\5m Sales Records.csv'


    
    with open(csv_file_path,'r') as file:
        reader = csv.DictReader(file)

        next(reader)
        i=0
        for row in reader:
            Country.objects.get_or_create(Country_name = row['Country'] , region=row['Region'] ) 
            
            
            print("data pass",i)
            i+=1
        
            






if __name__ == '__main__':
    run()