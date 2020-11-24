#MAIN
# This is the beginning of the code

#LIBRARIES
import simpy 
import random 
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
#from Router import Network
import time

#CLASSES
from my_modules.station import Station
from my_modules.charging_station import ChargingStation
from my_modules.bike import Bike, StationBike, DocklessBike, AutonomousBike
from my_modules.user import User, StationBasedUser, DocklessUser, AutonomousUser
from my_modules.data_interface import DataInterface
from my_modules.van import Van
from my_modules.demand_manager import DemandManager


#PARAMETERS/CONFIGURATION
mode=0 # 0 for StationBased / 1 for Dockless / 2 for Autonomous
n_bikes= 300

N_VANS=4
VAN_CAPACITY= 22

#network=Network()

# station information
stations_data=pd.read_excel('./data/bluebikes_stations.xlsx', index_col=None)
stations_data.drop([83],inplace=True) #This station has 0 docks
stations_data.reset_index(drop=True, inplace=True) #reset index

#charging station info -> For the moment, same than docking stations
charging_stations_data=pd.read_excel('./data/bluebikes_stations.xlsx', index_col=None)
charging_stations_data.drop([83],inplace=True) #This station has 0 docks
charging_stations_data.reset_index(drop=True, inplace=True) #reset index

#Rebalancing vans information
van_data=[]
for i in range(0,N_VANS):
    van_id= i
    capacity=VAN_CAPACITY
    lat= 42.3600018
    lon= -71.087598
    van=[van_id,capacity,lat,lon]
    van_data.append(van)



#bike information
bikes_data = [] 

if mode==1 or mode==2:
    #For dockless and autonomous the initial location is the lat,lon of a random station (placeholder)
    i=0
    while i<n_bikes: 
        rand_station=random.randint(0,len(stations_data)-1)
        lat=stations_data.iloc[rand_station]['Latitude']
        lon=stations_data.iloc[rand_station]['Longitude']
        bike=[i,lat,lon] 
        bikes_data.append(bike) 
        i+=1
elif mode==0:
    #For station based the initial location is defined by the id of a random station (placeholder)
    i=0
    while i<n_bikes:
        #We can only set to len(stations_data)-1 because length is 340 but the last station is the 339 (First row + deleted station)
        bike_station_id=random.randint(0,len(stations_data)-1)  #Warning! This does not check if the station is full     
        bike=[i,bike_station_id]    
        bikes_data.append(bike)
        i+=1

#Loads info from ODmatrix
OD_df=pd.read_excel('./data/output_sample.xlsx')


#DEFINITION OF CLASSES

class SimulationEngine: #Initialization and loading of data

    def __init__(self, env, stations_data, OD_data, bikes_data, charging_stations_data, van_data, datainterface, demandmanager): 
            self.env = env 
            self.stations_data=stations_data
            self.charging_stations_data=charging_stations_data
            self.van_data= van_data
            self.od_data=OD_data
            self.bikes_data=bikes_data

            self.stations = [] 
            self.charging_stations =[]
            self.vans=[]
            self.bikes = []
            self.users = []

            self.datainterface=datainterface 
            self.demandmanager=demandmanager
            #self.chargemanager=chargemanager

            self.start() 

    def start(self): 
            self.init_stations()
            self.init_charging_stations()
            self.init_vans()
            self.init_bikes()
            self.init_users()
            self.init_managers()

    def init_stations(self):
        #Generate and configure stations
            for station_id, station_data in self.stations_data.iterrows(): 
                station = Station(self.env, station_id)  
                station.set_capacity(station_data['Total docks']) 
                station.set_location(station_data['Latitude'], station_data['Longitude'])
                self.stations.append(station) 

    def init_charging_stations(self):
        #Generate and configure stations
            for station_id, station_data in self.charging_stations_data.iterrows(): 
                charging_station = ChargingStation(self.env, station_id)  
                charging_station.set_capacity(station_data['Total docks']) 
                charging_station.set_location(station_data['Latitude'], station_data['Longitude'])
                self.charging_stations.append(charging_station)
    
    def init_vans(self):
            for van_id, van_data in enumerate(self.van_data):
                van_id=van_data[0] 
                van = Van(self.env, van_id)  
                van.set_capacity(van_data[1]) 
                van.set_location(van_data[2], van_data[3])
                #print(van_id, van_data[1],van_data[2],van_data[3])
                self.vans.append(van)

    def init_bikes(self):
            #Generate and configure bikes
            for bike_id, bike_data in enumerate(self.bikes_data): 
                if mode == 0: #Station Based
                    bike = StationBike(self.env, bike_id) 
                    station_id = bike_data[1] #station id
                    self.stations[station_id].attach_bike(bike_id) #saves the bike in the station
                    bike.attach_station(station_id)  #saves the station in the bike
                    bike.set_location(self.stations[station_id].location[0],self.stations[station_id].location[1])  
                elif mode == 1: #Dockless
                    bike = DocklessBike(self.env, bike_id) 
                    bike.set_location(bike_data[1], bike_data[2])  #lat, lon
                elif mode == 2: #Autonomous
                    bike = AutonomousBike(self.env, bike_id,datainterface) 
                    bike.set_location(bike_data[1], bike_data[2]) #lat, lon
                self.bikes.append(bike) 

    def init_users(self):
            #Generate and configure users
            for index,row in self.od_data.iterrows(): 
                origin=[]
                destination=[]
                origin.append(row['start station latitude']) #origin lat
                origin.append(row['start station longitude']) #origin lon
                origin_np=np.array(origin)
                destination.append(row['end station latitude']) #destination lat
                destination.append(row['end station longitude']) #destination lon
                destination_np=np.array(destination)
                departure_time=row['elapsed time'] #departure time
                if mode == 0:
                    user = StationBasedUser(self.env, index, origin_np, destination_np, departure_time, datainterface)
                elif mode == 1:
                    user = DocklessUser(self.env, index, origin_np, destination_np, departure_time, datainterface)
                elif mode == 2:
                    user = AutonomousUser(self.env, index, origin_np, destination_np, departure_time, datainterface, demandmanager)
                user.start()   
                self.users.append(user) 
    def init_managers(self):
        self.datainterface.set_data(self.stations,self.charging_stations, self.bikes)
        self.demandmanager.set_data(self.bikes)
        #self.chargemanager.set_data(self.bikes)
        #self.chargemanager.start()
        
class Assets: #Put inside of City
    #location of bikes, situaition of stations
    #it is updated by user trips and the FleetManager
    def __init__(self,env):
        self.env=env

class RebalancingManager:
    #makes rebalancing decisions for SB and dockless
    def __init__(self,env):
        self.env=env
class DemandPredictionManager:
    #predictive rebalancing for autonomous
    def __init__(self,env):
        self.env=env
# class ChargeManager:
#     #makes recharging decisions
#     def __init__(self,env):
#         self.env=env

#     def set_data(self, bikes):
#         self.bikes = bikes
#     def start(self):
#         print('stating charge manager')
#         self.env.process(self.battery_checking())
        
#     def battery_checking(self):
#         print('started checking batteries')
#         while True:
#             for bike in self.bikes:
#                 if bike.battery < MIN_BATTERY_LEVEL:
#                     bike.autonomous_charge()
            

class FleetManager:
    #sends the decisions to the bikes
    #updates SystemStateData
    def __init__(self,env):
        self.env=env

#MAIN BODY - SIMULATION AND HISTORY GENERATION
env = simpy.Environment()
datainterface=DataInterface(env)
demandmanager=DemandManager(env)
#chargemanager=ChargeManager(env)
city = SimulationEngine(env, stations_data, OD_df, bikes_data, charging_stations_data, van_data, datainterface, demandmanager)
env.run(until=1000)