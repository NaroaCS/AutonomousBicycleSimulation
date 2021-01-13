
import random 
import numpy as np
import pandas as pd
import json

#PARAMETERS/CONFIGURATION
with open('config.json') as config_file:
    params = json.load(config_file)

n_bikes = params['n_bikes']

# station information
stations_data=pd.read_excel('./data/bluebikes_stations.xlsx', index_col=None)
stations_data.drop([83],inplace=True) #This station has 0 docks
stations_data.reset_index(drop=True, inplace=True) #reset index

suma=0

for station_id, station_data in stations_data.iterrows(): 
  suma += station_data['Total docks']
  print(station_id, station_data['Total docks'])
  


print(suma)

cols = ['n_bikes_max','c']
n=len(stations_data)-1
print(n)
stations = pd.DataFrame( columns = cols, index =range(n+1))

for station_id, station_data in stations_data.iterrows(): 
  stations.loc[station_id].n_bikes_max = (station_data['Total docks']*n_bikes)/suma
  stations.loc[station_id].c= 0
  
print (stations)

cols2= ['bike_id','station_id']
bikes_data = pd.DataFrame( columns = cols2, index=range(n_bikes))
i=0

while i<n_bikes:
  bike_station_id=random.randint(0,len(stations_data)-1)   
  if   stations.loc[bike_station_id].c < stations.loc[bike_station_id].n_bikes_max : 
    stations.loc[bike_station_id].c += 1  
    bikes_data.loc[i].bike_id= i
    bikes_data.loc[i].station_id= bike_station_id 
    i+=1

print (bikes_data.head())

#Save to Excel file
bikes_data.to_excel("./data/bikes_data.xlsx") 