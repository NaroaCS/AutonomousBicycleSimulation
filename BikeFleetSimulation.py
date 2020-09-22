#MAIN
# This is the beggining of the code

#LIBRARIES
import simpy #For sequential coding
import random 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from Router import Network

#PARAMETERS/CONFIGURATION
mode=2 # 0 for StationBased / 1 for Dockless / 2 for Autonomous
WALK_RADIUS = 50
n_bikes= 10

#map

network=Network()

#Testing_route
# from_lon=-71.058099
# from_lat=42.361942
# to_lon= -71.087446
# to_lat=42.360590
# route=network.get_route(from_lon, from_lat, to_lon, to_lat)
# print(route)

# station information
stations_data=pd.read_excel('bluebikes_stations.xlsx')

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
        station_id=24 # Set random station 
        bike=[i,station_id]    
        bikes_data.append(bike)

print(bikes_data)

#bike information for dockless and autonomous -> id and location(lat,lon)

#OD matrix
OD_df=pd.read_excel('output_sample.xlsx')

#Initialize bikes


#DEFINITION OF CLASSES
class SimulationEngine:
    def __init__(self, env, stations_data, OD_data, bikes_data): 
            self.env = env 
            #self.data = data
            self.stations_data=stations_data
            self.od_data=OD_data
            self.bikes_data=bikes_data

            self.stations = [] 
            self.bikes = []
            self.users = []

            self.start()

    def start(self): 
            self.init_stations()
            self.init_bikes()
            self.init_users()

    def init_stations(self):
            for station_id, station_data in enumerate(self.stations_data): 
                station = Station(self.env, station_id)  
                station.set_capacity(station_data[3]) 
                station.set_location(station_data[1], station_data[2]) #(lat,lon)
                self.stations.append(station) 
                print(station)

    def init_bikes(self):
            for bike_id, bike_data in enumerate(self.bikes_data): 
                #mode = bike_data['mode'] #Takes the mode 
                if mode == 0:
                    bike = StationBike(self.env, bike_id) 
                    station_id = bike_data[1] 
                    self.stations[station_id].lock_bike(bike_id) 
                    bike.attach_station(station_id)  
                    bike.set_location(self.stations[station_id].location)  #Check if this gives the proper input to set_loc 
                elif mode == 1:
                    bike = DocklessBike(self.env, bike_id) 
                    bike.set_location(bike_data[1], bike_data[2]) #lat,lon
                elif mode == 2:
                    bike = AutonomousBike(self.env, bike_id) 
                    bike.set_location(bike_data[1], bike_data[2]) 
                self.bikes.append(bike) 

    def init_users(self):
            datainterface=DataInterface(env) #Not sure why this is here
            origin=[]
            destination=[]
            for user_id, user_data in enumerate(self.od_data): 
                origin.append(user_data[1]) #origin lat
                origin.append(user_data[2]) #origin lon
                destination.append(user_data[3]) #destination lat
                destination.append(user_data[4]) #destination lon
                time=user_data[0] #departure time
                if mode == 0:
                    user = StationBasedUser(self.env, user_id, origin, destination, time, datainterface)
                elif mode == 1:
                    user = DocklessUser(self.env, user_id, origin, destination, time, datainterface)
                elif mode == 2:
                    user = AutonomousUser(self.env, user_id, origin, destination, time)
                user.start() 
                #user.set_data(self.data['grid'], self.stations, self.bikes)  
                self.users.append(user) 
                print(user)

class Bike:
    def __init__(self,env, bike_id):
        self.env=env
        self.bike_id=bike_id
        self.location=None
        self.user=None

    def set_location(self, lat, lon):
        self.location = [lat,lon]
    
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
        yield self.env.timeout(distance)
        self.location = destination
        #save this info in SystemStateData

    def dist(self, a, b): #delete after instering routing
        return np.linalg.norm(a - b)
       
class StationBike(Bike):
    def __init__(self,env,bike_id):
        super().__init__(env, bike_id)  
        self.station_id = None

    def attach_station(self, station_id):
        self.station_id = station_id

    def detach_station(self):
        self.station_id = None

    def register_unlock(self, user_id):
        self.set_user(user_id)
        self.detach_station()

    def register_lock(self, station_id):
        self.delete_user()
        self.attach_station(station_id)
    
    def docked(self):
        return self.station_id is not None

class DocklessBike(Bike):
    def __init__(self, env, bike_id):
        super().__init__(env, bike_id)        
        #self.init_state()

    def unlock(self, user_id):
        self.set_user(user_id)

    def lock(self):
        self.delete_user()

class AutonomousBike(Bike):
    def __init__(self,env, bike_id):
        super().__init__(env, bike_id)
        self.reserved=False
        
    
    def call(self, user_id):
         self.set_user(user_id)
         reserved= True

    def reserved(self):
        if (self.reservation_id is not None):
            return True

    def go_towards(self, destination_location):
        #This is for the demand prediction
        distance = self.dist(self.location, destination_location) #This should be routing
        yield self.env.timeout(distance)
        self.location = destination_location

    def autonomous_drive(self, user_location):
        distance = self.dist(self.location, user_location) #This should be routing
        yield self.env.timeout(distance)
        self.location =user_location
        #Save pickup and update
    def drop(self):
        self.delete_user()
        self.reserved= False
        
class Station:
    def __init__(self,env,station_id):
        self.env=env
        self.station_id=station_id
        self.location = None
        self.capacity = None

    def set_location(self, lat, lon):
        self.location = [lat,lon]

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

    def attach_bike(self, bike_id):
        if self.has_docks(): 
            self.n_bikes+=1 
            self.bikes.append(bike_id) 
            #Save in SystemStateData
        else:
            print('[%.2f] Station %d has no docks available' %
              (self.env.now, self.station_id))

    def detach_bike(self):
        if self.has_bikes(): 
            self.n_bikes-=1 
            bike_id=random.choice(self.bikes) 
            self.bikes.remove(bike_id) 
            #Save in SystemStateData
        else:
            print('[%.2f] Station %d has no bikes available' %
              (self.env.now, self.station_id))
        
class User:
    def __init__(self,env,user_id, origin, destination, time):
        self.env=env
        self.user_id=user_id
        self.location= None
        self.state=None #None, walking,waiting,biking
        self.event_setup_task = self.env.event() # ?¿ Here or in a start() function
        self.bike_id=None

        self.origin=None
        self.destination=None
        self.time=None
    
    def set_data(self, grid, stations, bikes):
        self.grid = grid
        self.stations = stations
        self.bikes = bikes

    def process(self):

        # 1-Init on origin
        yield self.env.process(self.init_user())


    def init_user(self):
        yield self.env.timeout(self.time) #waits until its the hour
        self.location = self.origin
        if self.print:
            print('[%.2f] User %d initialized at location [%.2f, %.2f]' %
                  (self.env.now, self.user_id, *self.location))
                  
    def walk_to(self, location):
        #Here it should call routing
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)
        self.location = location

    def ride_bike_to(self, location):
        bike = self.bikes[self.bike_id]
        yield self.env.process(bike.ride(location)) 
        self.location = location
    
    def dist(self, a, b):
        return np.linalg.norm(a - b)

class StationBasedUser(User):
    def __init__(self, env, user_id, origin, destination, time, datainterface):
        super().__init__(env, user_id, origin, destination, time)
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
            yield self.event_select_station
            #station = self.stations[self.station_id]

            # 3-Walk to origin station
            yield self.env.process(self.walk_to(station_location))

            # 4-unlock bike
            yield self.env.process(self.interact_bike(action='unlock'))
            
        self.event_interact_bike = self.env.event()
        visited_stations.clear() #here we should zero it because one might do a round trip
        
        while not self.event_interact_bike.triggered:
            # 5-Select destination station
            [station, station_location, visited_stations]=self.select_end_station(self.location,self.visited_stations)
            yield self.event_select_station
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

    #def update_station_info(self, location): 
        # values = []
        # for station in self.stations:
        #     station_id = station.station_id
        #     has_bikes = station.has_bikes()
        #     has_docks = station.has_docks()
        #     visited = station_id in self.visited_stations
        #     distance = self.dist(location, station.location) 
        #     walkable = distance < WALK_RADIUS
        #     values.append((station_id, has_bikes, has_docks,
        #                    visited, distance, walkable))
        # labels = ['station_id', 'has_bikes', 'has_docks',
        #           'visited', 'distance', 'walkable']
        # types = [int, int, int,
        #          int, float, int]
        # dtype = list(zip(labels, types))
        # self.station_info = np.array(values, dtype=dtype)

    #def select_station(self, aim):
        # self.event_select_station = self.env.event()
        # if aim=='origin':
        #     location=self.location
        # else:
        #     location=self.destination

        # self.update_station_info(location)

        # for e in np.sort(self.station_info, order='distance'):
        #     if aim == 'origin':
        #         valid = e['has_bikes'] and not e['visited'] and e['walkable']
        #     else:
        #         valid = e['has_docks'] and not e['visited'] and e['walkable']
        #     if valid:
        #         self.station_id = e['station_id']
        #         self.visited_stations.append(self.station_id)
        #         self.event_select_station.succeed()
                
        # if not self.event_select_station.triggered:
        #     print("No bikes/docks found in a walkable distance")

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
                station.unlock_bike(self.bike_id)
            else:
                self.bikes[self.bike_id].register_lock(self.station_id)
                station.lock_bike(self.bike_id)

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
    def __init__(self, env, user_id, origin, destination, time, datainterface):
        super().__init__(env, user_id, origin, destination, time)
        self.datainterface=datainterface
    def start(self):
        #super().start()

        # DOCKLESS
        self.dockless_bike_id = None
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
            [dockless_bike,dockless_bike_location]=self.select_dockless_bike(self.location)
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


    #def update_bike_info(self): 
        # values = []
        # for bike in self.bikes:
        #     if isinstance(bike, DocklessBike):
        #         bike_id = bike.bike_id
        #         rented = bike.rented()
        #         distance = self.dist(self.location, bike.location)
        #         walkable = distance < WALK_RADIUS
        #         values.append((bike_id, rented, distance, walkable))
        # labels = ['bike_id', 'rented', 'distance', 'walkable']
        # types = [int, int, float, int]
        # dtype = list(zip(labels, types))
        # self.bike_info = np.array(values, dtype=dtype)

    #def select_dockless_bike(self):
        # self.event_select_dockless_bike = self.env.event()
        # self.update_bike_info()
        # for e in np.sort(self.bike_info, order='distance'):
        #     valid = not e['rented'] and e['walkable']
        #     if valid:
        #         self.dockless_bike_id = e['bike_id']
        #         self.event_select_dockless_bike.succeed()

        # if not self.event_select_dockless_bike.triggered:
        #     print("No bikes in walkable distance")
           
    def select_dockless_bike(self,location):
        selected_bike_info=self.datainterface.select_dockless_bike(location)
        return selected_bike_info

    def unlock_bike(self):
        dockless_bike = self.bikes[self.dockless_bike_id]
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
    def __init__(self, env, user_id, origin, destination, time):
        super().__init__(env, user_id, origin, destination, time)

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
        self.call_autonomous_bike()
        yield self.event_call_autonomous_bike

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


    def update_bike_info(self):  ##Isinstannce???
        values = []
        for bike in self.bikes:
            if isinstance(bike, AutonomousBike):
                bike_id = bike.bike_id
                rented = bike.rented()
                distance = self.dist(self.location, bike.location)
                walkable = distance < WALK_RADIUS
                values.append((bike_id, rented, distance, walkable))
        labels = ['bike_id', 'rented', 'distance', 'walkable']
        types = [int, int, float, int]
        dtype = list(zip(labels, types))
        self.bike_info = np.array(values, dtype=dtype)

    def call_autonomous_bike(self):  #This should be transferred to the demand manager / Here it is not 'walkabke'
        self.event_call_autonomous_bike = self.env.event()
        self.update_bike_info()
        for e in np.sort(self.bike_info, order='distance'):
            valid = not e['rented'] and e['walkable']
            if valid:
                self.bike_id = e['bike_id']
                self.bikes[self.bike_id].call(self.user_id)
                self.event_call_autonomous_bike.succeed()

        if not self.event_call_autonomous_bike.triggered:
            print("No autonomous bikes in XX miles")
    

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

    def set_data(self, grid, stations, bikes):
        self.grid = grid
        self.stations = stations
        self.bikes = bikes

    def dist(self, a, b):
        return np.linalg.norm(a - b)

    def select_start_station(self,location,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_bikes = station.has_bikes()
            visited = station_id in visited_stations
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.latitude
            lon=station.longitude
            values.append((station_id, has_bikes,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_bikes',
                  'visited', 'distance', 'walkable', 'lat','lon']
        types = [int, int,
                 int, float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        self.event_select_station = self.env.event()

        for e in np.sort(station_info, order='distance'):
            valid = e['has_bikes'] and not e['visited'] and e['walkable']
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)   
                self.event_select_station.succeed()        
                
        if not self.event_select_station.triggered:
            print("No bikes found in a walkable distance")
        station_location=[lat,lon]
        return [station_id, station_location, visited_stations] 

    def select_end_station(self,location,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_docks = station.has_docks()
            visited = station_id in visited_stations
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.latitude
            lon=station.longitude
            values.append((station_id, has_docks,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_docks',
                  'visited', 'distance', 'walkable', 'lat','lon']
        types = [int, int, 
                 int, float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        self.event_select_station = self.env.event()

        for e in np.sort(station_info, order='distance'):
            valid = e['has_docks'] and not e['visited'] and e['walkable']
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)
                self.event_select_station.succeed()        
                
        if not self.event_select_station.triggered:
            print("No docks found in a walkable distance")
        station_location=[lat,lon]
        return [station_id,station_location,visited_stations]

    def select_dockless_bike(self,location):

        values = []

        for bike in self.bikes:
            if isinstance(bike, DocklessBike):
                bike_id = bike.bike_id
                rented = bike.rented()
                distance = self.dist(location, bike.location)
                walkable = distance < WALK_RADIUS
                lat=bike.latitude
                lon=bike.longitude
                values.append((bike_id, rented, distance, walkable,lat,lon))
        labels = ['bike_id', 'rented', 'distance', 'walkable','lat','lon']
        types = [int, int, float, int,float,float]
        dtype = list(zip(labels, types))
        bike_info = np.array(values, dtype=dtype)

        self.event_select_dockless_bike = self.env.event()

        for e in np.sort(bike_info, order='distance'):
            valid = not e['rented'] and e['walkable']
            if valid:
                dockless_bike_id = e['bike_id']
                lat=e['lat']
                lon=e['lon']
                self.event_select_dockless_bike.succeed()

        if not self.event_select_dockless_bike.triggered:
            print("No bikes in walkable distance")
        bike_location=[lat,lon]
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
class FleetManager:
    #sends the decisions to the bikes
    #updates SystemStateData
    def __init__(self,env):
        self.env=env

#MAIN BODY - SIMULATION AND HISTORY GENERATION
env = simpy.Environment()
city = SimulationEngine(env, stations_data, OD_df, bikes_data)
env.run(until=1000)