#MAIN
# This is the beggining of the code

#LIBRARIES
import simpy #For sequential coding
import random 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from Router import Network
import time

#PARAMETERS/CONFIGURATION
mode=0 # 0 for StationBased / 1 for Dockless / 2 for Autonomous
n_bikes= 300

WALK_RADIUS = 500
MAX_AUTONOMOUS_RADIUS= 1000
WALKING_SPEED= 5/3.6 #m/s
RIDING_SPEED = 15/3.6 #m/s
AUT_DRIVING_SPEED = 10/3.6 #m/s

#map

network=Network()

#Testing_route

from_lon=-71.058099
from_lat=42.361942
to_lon= -71.087446
to_lat=42.360590
route=network.get_route(from_lon, from_lat, to_lon, to_lat)
d=route['cum_distances'][-1]
print(route)
print(d)

# station information
stations_data=pd.read_excel('bluebikes_stations.xlsx', index_col=None)
stations_data.drop([83],inplace=True) #This station has 0 docks
stations_data.reset_index(drop=True, inplace=True) #reset index

#bike information for SB -> id and initial station id
bikes_data = [] 

if mode==1 or mode==2:
    i=0
    while i<n_bikes:
        bike=[i,0,0] #Set random locatio (lat,lon)
        bikes_data.append(bike) 
        i+=1
elif mode==0:
    i=0
    while i<n_bikes:
        #We can only set to len(stations_data)-1 because length is 340 but the last station is the 339 (First row + deleted station)
        bike_station_id=random.randint(0,len(stations_data)-1)  #This does not check if full      
        bike=[i,bike_station_id]    
        bikes_data.append(bike)
        i+=1

#bike information for dockless and autonomous -> id and location(lat,lon)

#OD matrix
OD_df=pd.read_excel('output_sample.xlsx')
print(OD_df.head())


#DEFINITION OF CLASSES
class SimulationEngine:
    def __init__(self, env, stations_data, OD_data, bikes_data, datainterface, demandmanager): 
            self.env = env 
            #self.data = data
            self.stations_data=stations_data
            self.od_data=OD_data
            self.bikes_data=bikes_data

            self.stations = [] 
            self.bikes = []
            self.users = []

            self.datainterface=datainterface 
            self.demandmanager=demandmanager

            self.start()

    def start(self): 
            self.init_stations()
            self.init_bikes()
            self.init_users()
            self.init_managers()

    def init_stations(self):
            for station_id, station_data in self.stations_data.iterrows(): 
                station = Station(self.env, station_id)  
                station.set_capacity(station_data['Total docks']) 
                station.set_location(station_data['Latitude'], station_data['Longitude'])
                self.stations.append(station) 

    def init_bikes(self):
            for bike_id, bike_data in enumerate(self.bikes_data): 
                #mode = bike_data['mode'] #Takes the mode 
                if mode == 0:
                    bike = StationBike(self.env, bike_id) 
                    station_id = bike_data[1]
                    self.stations[station_id].attach_bike(bike_id) 
                    bike.attach_station(station_id)  
                    bike.set_location(self.stations[station_id].location[0],self.stations[station_id].location[1])  #Check if this gives the proper input to set_loc 
                elif mode == 1:
                    bike = DocklessBike(self.env, bike_id) 
                    bike.set_location(bike_data[1], bike_data[2]) #lat,lon
                elif mode == 2:
                    bike = AutonomousBike(self.env, bike_id) 
                    bike.set_location(bike_data[1], bike_data[2]) 
                self.bikes.append(bike) 

    def init_users(self):
 
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
                    user = AutonomousUser(self.env, index, origin_np, destination_np, departure_time, demandmanager)
                user.start() 
                user.set_data(self.stations, self.bikes)  
                self.users.append(user) 
    def init_managers(self):
        self.datainterface.set_data(self.stations,self.bikes)
        self.demandmanager.set_data(self.bikes)

class Bike:
    def __init__(self,env, bike_id):
        self.env=env
        self.bike_id=bike_id
        self.location=None
        self.user=None
        self.busy=False

    def set_location(self, lat, lon):
        self.location = np.array([lat,lon])
    
    # def update_location(self,location):
    #     self.location = location

    def update_user(self,user_id):
        self.user = user_id

    def delete_user(self):
        self.user = None

    def vacant(self):
        if (self.user is None):
            return True

    def ride(self,destination):
        #Here it should call the routing algotithm
        # time=routing(self.location,destination,bikingspeed)
        distance = self.dist(self.location, destination)
        time=distance/RIDING_SPEED
        yield self.env.timeout(time)
        self.location = destination
        #save this info in SystemStateData

    def dist(self, a, b):
        #return np.linalg.norm(a - b)
        route=network.get_route(a[1], a[0], b[1], b[0])
        d=route['cum_distances'][-1]
        return d
        
       
class StationBike(Bike):
    def __init__(self,env,bike_id):
        super().__init__(env, bike_id)  
        self.station_id = None

    def attach_station(self, station_id):
        self.station_id = station_id

    def detach_station(self):
        self.station_id = None

    def register_unlock(self, user_id):
        self.update_user(user_id)
        self.detach_station()
        self.busy=True

    def register_lock(self, station_id):
        self.delete_user()
        self.attach_station(station_id)
        self.busy=False
    
    def docked(self):
        return self.station_id is not None

class DocklessBike(Bike):
    def __init__(self, env, bike_id):
        super().__init__(env, bike_id)        
        #self.init_state()

    def unlock(self, user_id):
        self.set_user(user_id)
        self.busy=True

    def lock(self):
        self.delete_user()
        self.busy=False

class AutonomousBike(Bike):
    def __init__(self,env, bike_id):
        super().__init__(env, bike_id)
        self.reserved=False
        
    
    def call(self, user_id):
         self.set_user(user_id)
         self.reserved= True            #Maybe we dont need this anymore
         self.busy=True

    def reserved(self):
        if (self.reservation_id is not None):
            return True

    def go_towards(self, destination_location):
        #This is for the demand prediction
        distance = self.dist(self.location, destination_location) 
        time=distance/AUT_DRIVING_SPEED
        yield self.env.timeout(time)
        self.location = destination_location

    def autonomous_drive(self, user_location):
        distance = self.dist(self.location, user_location)
        time=distance/AUT_DRIVING_SPEED
        yield self.env.timeout(time)
        self.location =user_location
        #Save pickup and update
    def drop(self):
        self.delete_user()
        self.reserved= False   #Maybe we dont need this anymore
        self.busy=False

        
class Station:
    def __init__(self,env,station_id):
        self.env=env
        self.station_id=station_id
        self.location = None
        self.capacity = 0
        self.n_bikes= 0

        self.bikes = []

    def set_location(self, lat, lon):
        self.location = np.array([lat,lon])

    def set_capacity(self, capacity):
        self.capacity = capacity
   
    def has_bikes(self):
        return self.n_bikes > 0

    def has_docks(self):
        return self.capacity - self.n_bikes > 0

    def empty(self):
        return self.n_bikes == 0

    def full(self):
        return self.n_bikes == self.capacity
    
    def choose_bike(self):  # Selects any bike 
        return random.choice(self.bikes)

    def attach_bike(self, bike_id):
        if self.has_docks(): 
            self.n_bikes+=1 
            self.bikes.append(bike_id) 
            #Save in SystemStateData
        else:
            print('[%.2f] Station %d has no docks available' %
              (self.env.now, self.station_id))

    def detach_bike(self, bike_id):
        if self.has_bikes(): 
            self.n_bikes-=1 
            bike_id=random.choice(self.bikes) 
            self.bikes.remove(bike_id) 
            #Save in SystemStateData
        else:
            print('[%.2f] Station %d has no bikes available' %
              (self.env.now, self.station_id))
        
class User:
    def __init__(self,env,user_id, origin, destination, departure_time):
        self.env=env
        self.user_id=user_id
        self.location= None
        self.state=None #None, walking,waiting,biking
        self.event_setup_task = self.env.event() # ?¿ Here or in a start() function
        self.bike_id=None

        self.stations=[]
        self.bikes=[]

        self.origin=origin
        self.destination=destination
        self.departure_time=departure_time
    
    def set_data(self, stations, bikes):
        self.stations = stations
        self.bikes = bikes

    def process(self):

        # 1-Init on origin
        yield self.env.process(self.init_user())

    def init_user(self):
        yield self.env.timeout(self.departure_time) #waits until its the hour
        self.location = self.origin
        print('[%.2f] User %d initialized at location [%.4f, %.4f]' % (self.env.now, self.user_id, self.location[0], self.location[1]))
                  
    def walk_to(self, location):
        #Here it should call routing
        distance = self.dist(self.location, location)
        time=distance/WALKING_SPEED
        yield self.env.timeout(time)
        self.location = location
        print('[%.2f] User %d walked from [%.4f, %.4f] to location [%.4f, %.4f]' % (self.env.now, self.user_id, self.location[0], self.location[1], location[0], location[1]))

    def ride_bike_to(self, location):
        bike = self.bikes[self.bike_id]
        print('[%.2f] User %d biking from [%.4f, %.4f] to location [%.4f, %.4f]' % (self.env.now, self.user_id, self.location[0], self.location[1], bike.location[0], bike.location[1]))
        yield self.env.process(bike.ride(location)) 
        self.location = location
        
    
    def dist(self, a, b):
        #return np.linalg.norm(a - b)
        route=network.get_route(a[1], a[0], b[1], b[0])
        d=route['cum_distances'][-1]
        return d

class StationBasedUser(User):
    def __init__(self, env, user_id, origin, destination, departure_time, datainterface):
        super().__init__(env, user_id, origin, destination, departure_time)
        self.datainterface=datainterface

    def start(self):
        #super().start()

        # STATION-BASED
        
        self.station_id = None
        self.event_select_station = self.env.event()
        self.event_interact_bike = self.env.event()
        self.visited_stations = []
        #self.station_history = []

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on origin
        yield self.env.process(super().process())
        
        self.event_interact_bike = self.env.event() 
        while not self.event_interact_bike.triggered:
            # 2-Select origin station
            [station, station_location, visited_stations]=self.select_start_station(self.location,self.visited_stations)
            self.station_id=station
            print('[%.2f] User %d selected start station [%.4f, %.4f]' % (self.env.now, self.user_id, station_location[0],station_location[1]))
            #yield self.event_select_station
            station = self.stations[self.station_id]

            # 3-Walk to origin station
            yield self.env.process(self.walk_to(station_location))

            # 4-unlock bike
            yield self.env.process(self.interact_bike(action='unlock'))
            
        self.event_interact_bike = self.env.event()
        visited_stations.clear() #here we should zero it because one might do a round trip
        
        while not self.event_interact_bike.triggered:
            # 5-Select destination station
            [station, station_location, visited_stations]=self.select_end_station(self.location,self.visited_stations)
            print('[%.2f] User %d selected end station %d' % (self.env.now, self.user_id, self.station_id))
            #yield self.event_select_station
            #station = self.stations[self.station_id]

            # 6-Ride bike
            yield self.env.process(self.ride_bike_to(station_location))

            # 7-lock bike
            yield self.env.process(self.interact_bike(action='lock'))

        # 8-Walk to destination
        yield self.env.process(self.walk_to(self.destination))
    
        # 9-Save state
        # self.save_state()

        # # 10-Finish
        yield self.env.timeout(10)
        # if self.print:
        #     print('[%.2f] User %d working' % (self.env.now, self.user_id))
    
    def select_start_station(self,location,visited_stations):
        selected_station_info=self.datainterface.select_start_station(location,visited_stations)
        return selected_station_info

    def select_end_station(self,location,visited_stations):
        selected_station_info=self.datainterface.select_end_station(location,visited_stations)
        return selected_station_info


    def interact_bike(self, action):
        station = self.stations[self.station_id]

        #Check if there are still bikes/docks at arrival
        if action=='unlock':
            valid=station.has_bikes()
        else:
            valid=station.has_docks()
    
        if valid:
            if action == 'unlock':
                self.bike_id = station.choose_bike()
                self.bikes[self.bike_id].register_unlock(self.user_id) 
                station.detach_bike(self.bike_id)
            else:
                self.bikes[self.bike_id].register_lock(self.station_id)
                station.attach_bike(self.bike_id)

            self.event_interact_bike.succeed()

            yield self.env.timeout(1)
        else:
            # self.time_interact_bike = None
            # if self.print:
            #     print('[%.2f] Station %d has zero %s available' %
            #            (self.env.now, self.station_id, 'bikes' if action == 'unlock' else 'docks'))
            # yield self.env.timeout(3)
            print("There were no bikes/docks at arrival!")
              
class DocklessUser(User):
    def __init__(self, env, user_id, origin, destination, departure_time, datainterface):
        super().__init__(env, user_id, origin, destination, departure_time)
        self.datainterface=datainterface
    def start(self):
        #super().start()

        # DOCKLESS
        #self.dockless_history = []

        self.event_select_dockless_bike = self.env.event()
        self.event_unlock_bike = self.env.event()

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on origin
        yield self.env.process(super().process())

        while not self.event_unlock_bike.triggered:
            # 2-Select dockless bike
            [dockless_bike_id,dockless_bike_location]=self.select_dockless_bike(self.location)
            self.bike_id=dockless_bike_id
            yield self.event_select_dockless_bike
            #dockless_bike = self.bikes[self.dockless_bike_id]

            # 3-Walk to dockless bike
            yield self.env.process(self.walk_to(dockless_bike_location))

            # 4-Unlock bike
            yield self.env.process(self.unlock_bike())

        # 5-Ride bike
        yield self.env.process(self.ride_bike_to(self.destination))

        # 6-Drop bike
        self.lock_bike()

        # 7-Save state
        #self.save_state()

        # # 8-Finish
        yield self.env.timeout(10)
        # if self.print:
        #     print('[%.2f] User %d working' % (self.env.now, self.user_id))
           
    def select_dockless_bike(self,location):
        selected_bike_info=self.datainterface.select_dockless_bike(location)
        return selected_bike_info

    def unlock_bike(self,dockless_bike_id):
        dockless_bike = self.bikes[self.bike_id]
        if not dockless_bike.rented():
            yield self.env.timeout(1)
            self.bike_id = dockless_bike.bike_id
            dockless_bike.unlock(self.user_id)
            #HERE IT DOESNT SAVE THAT IT HAS BEEN RENTED
            self.event_unlock_bike.succeed()
        else:
            yield self.env.timeout(3)
            print('Bike has already been rented')

    def lock_bike(self):
        bike = self.bikes[self.bike_id]
        bike.lock()

class AutonomousUser(User):
    def __init__(self, env, user_id, origin, destination, departure_time,demandmanager):
        super().__init__(env, user_id, origin, destination, departure_time)
        self.demandmanager=demandmanager

    def start(self):
        #super().start()

        # AUTONOMOUS
        self.event_call_autonomous_bike = self.env.event()
       # self.autonomous_history = []

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on origin
        yield self.env.process(super().process())

        # 2-Call autonomous bike
        [autonomous_bike_id,autonomous_bike_location]=self.call_autonomous_bike(self.location)
        self.bike_id=autonomous_bike_id
        #yield self.event_call_autonomous_bike

        # 3-Wait for autonomous bike
        autonomous_bike = self.bikes[self.bike_id]
        yield self.env.process(autonomous_bike.autonomous_move(self.location))

        # 4-Ride bike
        yield self.env.process(self.ride_bike_to(self.destination))

        # 5-Drop bike
        self.drop_bike()

        # 6-Save state
        #self.save_state()

        # 7-Finish
        yield self.env.timeout(10)
        # if self.print:
        #     print('[%.2f] User %d working' % (self.env.now, self.user_id))


    def call_autonomous_bike(self, location):  
        assigned_bike_info=self.demandmanager.assign_autonomous_bike(location)
        return assigned_bike_info

    def drop_bike(self):
        bike = self.bikes[self.bike_id]
        bike.drop()

class Assets: #Put inside of City
    #location of bikes, situaition of stations
    #it is updated by user trips and the FleetManager
    def __init__(self,env):
        self.env=env

class DataInterface:
    #retreives info from SystemData
    def __init__(self,env):
        self.env=env

    def set_data(self, stations, bikes):
        #self.grid = grid
        self.stations = stations
        self.bikes = bikes

    def dist(self, a, b):
        #return np.linalg.norm(a - b)
        route=network.get_route(a[1], a[0], b[1], b[0])
        d=route['cum_distances'][-1]
        return d
      

    def select_start_station(self,location,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_bikes = station.has_bikes()
            visited = station_id in visited_stations
            #print('Calculating distance from [%.6f, %.6f] to [%.6f, %.6f]' % (location[0],location[1], station.location[0],station.location[1]))
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.location[0]
            lon=station.location[1]
            values.append((station_id, has_bikes,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_bikes',
                  'visited', 'distance', 'walkable', 'lat','lon']
        types = [int, int,
                 int, float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        select_succeeded = 0

        for e in np.sort(station_info, order='distance'):
            valid = e['has_bikes'] and not e['visited'] and e['walkable']
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)
                select_succeeded = 1   
                break         
  
        if select_succeeded == 0: 
            print("No bikes found in a walkable distance")
        station_location=np.array([lat,lon])

        return [station_id, station_location, visited_stations] 

    def select_end_station(self,location,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_docks = station.has_docks()
            visited = station_id in visited_stations
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.location[0]
            lon=station.location[1]
            values.append((station_id, has_docks,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_docks',
                  'visited', 'distance', 'walkable', 'lat','lon']
        types = [int, int, 
                 int, float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        select_succeeded = 0

        for e in np.sort(station_info, order='distance'):
            valid = e['has_docks'] and not e['visited'] and e['walkable']
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)
                select_succeeded = 1        
                
        if select_succeeded == 0:
            print("No docks found in a walkable distance")
        station_location=np.array([lat,lon])
        return [station_id,station_location,visited_stations]

    def select_dockless_bike(self,location):

        values = []

        for bike in self.bikes:
            if isinstance(bike, DocklessBike):
                bike_id = bike.bike_id
                rented = bike.rented()
                distance = self.dist(location, bike.location)
                walkable = distance < WALK_RADIUS
                lat=bike.location[0]
                lon=bike.location[1]
                values.append((bike_id, rented, distance, walkable,lat,lon))
        labels = ['bike_id', 'rented', 'distance', 'walkable','lat','lon']
        types = [int, int, float, int,float,float]
        dtype = list(zip(labels, types))
        bike_info = np.array(values, dtype=dtype)

        select_dockless_bike_succeeded = 0

        for e in np.sort(bike_info, order='distance'):
            valid = not e['rented'] and e['walkable']
            if valid:
                dockless_bike_id = e['bike_id']
                lat=e['lat']
                lon=e['lon']
                select_dockless_bike_succeeded = 1

        if select_dockless_bike_succeeded == 0:
            print("No bikes in walkable distance")
        bike_location=np.array([lat,lon])
        return [dockless_bike_id,bike_location]

class RebalancingManager:
    #makes rebalancing decisions for SB and dockless
    def __init__(self,env):
        self.env=env
class DemandPredictionManager:
    #predictive rebalancing for autonomous
    def __init__(self,env):
        self.env=env
class ChargeManager:
    #makes recharging decisions
    def __init__(self,env):
        self.env=env
class DemandManager:
    #receives orders from users and decides which bike goes
    def __init__(self,env):
        self.env=env
    
    def set_data(self, bikes):
        #self.grid = grid
        self.bikes = bikes

    def dist(self, a, b):
        #return np.linalg.norm(a - b)
        route=network.get_route(a[1], a[0], b[1], b[0])
        d=route['cum_distances'][-1]
        return d
      

    def assign_autonomous_bike(self, location):
        values = []

        for bike in self.bikes:
            if isinstance(bike, DocklessBike):
                bike_id = bike.bike_id
                rented = bike.rented()
                distance = self.dist(location, bike.location)
                reachable = distance < MAX_AUTONOMOUS_RADIUS
                lat=bike.location[0]
                lon=bike.location[1]
                values.append((bike_id, rented, distance, reachable,lat,lon))
        labels = ['bike_id', 'rented', 'distance', 'reachable','lat','lon']
        types = [int, int, float, int,float,float]
        dtype = list(zip(labels, types))
        bike_info = np.array(values, dtype=dtype)

        select_autonomous_bike_succeeded = 0

        for e in np.sort(bike_info, order='distance'):
            valid = not e['rented'] and e['reachable']
            if valid:
                autonomous_bike_id = e['bike_id']
                lat=e['lat']
                lon=e['lon']
                select_autonomous_bike_succeeded = 1

        if select_autonomous_bike_succeeded == 0:
            print("No bikes in"+ str(MAX_AUTONOMOUS_RADIUS) +"distance")
        bike_location=np.array([lat,lon])
        return [autonomous_bike_id,bike_location]

class FleetManager:
    #sends the decisions to the bikes
    #updates SystemStateData
    def __init__(self,env):
        self.env=env

#MAIN BODY - SIMULATION AND HISTORY GENERATION
env = simpy.Environment()
datainterface=DataInterface(env)
demandmanager=DemandManager(env)
city = SimulationEngine(env, stations_data, OD_df, bikes_data, datainterface, demandmanager)
env.run(until=1000)