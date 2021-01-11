import simpy 
import numpy as np
import pandas as pd
import json
#from .Router import Network
#from .Graph import Graph
from .Location import Location


from .Bike import Bike, StationBike, DocklessBike, AutonomousBike
from .User import User, StationBasedUser, DocklessUser, AutonomousUser

#network=Graph()

with open('config.json') as config_file:
    params = json.load(config_file)

WALK_RADIUS =  params['WALK_RADIUS'] #3500Just to try the dockless mode !
MAX_AUTONOMOUS_RADIUS= params['MAX_AUTONOMOUS_RADIUS'] 
MIN_BATTERY_LEVEL= params['MIN_BATTERY_LEVEL'] 

MIN_N_BIKES= params['MIN_N_BIKES'] 
MIN_N_DOCKS = params['MIN_N_DOCKS'] 


class DataInterface:

    def __init__(self,env, network):
        self.env=env
        self.network= network

    def set_data(self, stations, charging_stations, bikes):
        self.stations = stations
        self.bikes = bikes
        self.charging_stations= charging_stations

    def dist(self, a, b):
        a = Location(a[1], a[0])
        b = Location(b[1], b[0])
        d = self.network.get_shortest_path_length(a,b)
        return d
      
    def select_start_station(self,location,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_bikes = station.has_bikes()
            visited = station_id in visited_stations
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
                station_location=np.array([lat,lon]) 
                break         
  
        if select_succeeded == 0: 
            print('[%.2f] No bikes in a walkable distance' %
              (self.env.now))
            station_id=None
            station_location=None

        return [station_id, station_location, visited_stations] 
    
    def magic_bike(self, location, visited_stations):

        values = []
        for station in self.stations:
            station_id = station.station_id
            n_bikes= station.n_bikes
            n_docks=station.capacity - station.n_bikes
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.location[0]
            lon=station.location[1]
            values.append((station_id, n_bikes,
                           n_docks, distance, walkable, lat, lon))
        labels = ['station_id', 'n_bikes', 'n_docks'
                 , 'distance', 'walkable', 'lat','lon']
        types = [int, int, int,
                  float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        valid_source_found =0

        for e in np.sort(station_info, order='distance'):
            valid_source = e['n_bikes'] > MIN_N_BIKES
            if valid_source:
                source_station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                valid_source_found = 1
                #source_station_location=np.array([lat,lon]) 
                break

        if valid_source_found == 0:
            print('[%.2f] No stations found as source of magic bike' %
              (self.env.now))
            return [None, None, visited_stations]


        valid_target_found = 0
        for e in np.sort(station_info, order='distance'):
            valid_target= e['n_docks'] > 0 and e['walkable']
            if valid_target:
                target_station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                target_station_location=np.array([lat,lon]) 
                visited_stations.append(target_station_id)
                valid_target_found =1 
                break

        if valid_target_found == 0:
            print('[%.2f] No stations found as target for magic bike' %
              (self.env.now))
            return [None, None, visited_stations]

        #take random bike from source
        bike_id= self.station_choose_bike(source_station_id)
        self.station_detach_bike(source_station_id,bike_id)
        
        #put that bike on target station
        self.station_attach_bike(target_station_id, bike_id)

        ##### WHERE DO WE SAVE THE nº of magic trips???? #######

        #return target station info
        return [target_station_id,target_station_location,visited_stations]






    def select_end_station(self,destination,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_docks = station.has_docks()
            visited = station_id in visited_stations
            distance = self.dist(destination, station.location) 
            walkable = distance < WALK_RADIUS # ---> Once that ou're in the bike you have to leave it even if it's very far
            lat=station.location[0]
            lon=station.location[1]
            values.append((station_id, has_docks,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_docks',
                  'visited', 'distance', 'walkable','lat','lon']
        types = [int, int, 
                 int, float,int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        select_succeeded = 0

        for e in np.sort(station_info, order='distance'):
            valid = e['has_docks'] and e['walkable'] and not e['visited'] 
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)
                select_succeeded = 1
        if select_succeeded == 0: 
            print('[%.2f] No docks in a walkable distance' %
              (self.env.now))
            station_id=None
            station_location=None      
                
        station_location=np.array([lat,lon])
        return [station_id,station_location,visited_stations]

    def magic_dock(self, location, visited_stations):

        values = []
        for station in self.stations:
            station_id = station.station_id
            n_bikes= station.n_bikes
            n_docks=station.capacity - station.n_bikes
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.location[0]
            lon=station.location[1]
            values.append((station_id, n_bikes,
                           n_docks, distance, walkable, lat, lon))
        labels = ['station_id', 'n_bikes', 'n_docks'
                 , 'distance', 'walkable', 'lat','lon']
        types = [int, int, int,
                  float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        valid_target_found =0 
        #target for the bike that will be moved
        for e in np.sort(station_info, order='distance'):
            valid_target = e['n_docks'] > MIN_N_DOCKS
            if valid_target:
                target_station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                #target_station_location=np.array([lat,lon]) 
                valid_target_found =1
                break

        if valid_target_found == 0:
            print('[%.2f] No stations found as target of magic bike' %
              (self.env.now))
            return [None, None, visited_stations]

        valid_source_found =0 

        #Source of the bike -> it's where  the user will go because it's where a dock becomes available
        for e in np.sort(station_info, order='distance'):
            valid_source= e['n_bikes'] > 0 and e['walkable']
            if valid_source:
                source_station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                source_station_location=np.array([lat,lon]) 
                visited_stations.append(source_station_id)
                valid_source_found = 1
                break

        if valid_source_found == 0:
            print('[%.2f] No stations found as source of magic bike' %
              (self.env.now))
            return [None, None, visited_stations]

        #take random bike from source
        bike_id= self.station_choose_bike(source_station_id)
        self.station_detach_bike(source_station_id,bike_id)
        
        #put that bike on target station
        self.station_attach_bike(target_station_id, bike_id)

        ##### WHERE DO WE SAVE THE nº of magic trips???? #######

        #return source station info
        return [source_station_id,source_station_location,visited_stations]

    def notwalkable_dock(self,destination,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_docks = station.has_docks()
            visited = station_id in visited_stations
            distance = self.dist(destination, station.location) 
            walkable = distance < WALK_RADIUS # ---> Once that ou're in the bike you have to leave it even if it's very far
            lat=station.location[0]
            lon=station.location[1]
            values.append((station_id, has_docks,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_docks',
                  'visited', 'distance', 'walkable','lat','lon']
        types = [int, int, 
                 int, float,int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        select_succeeded = 0

        for e in np.sort(station_info, order='distance'):
            valid = e['has_docks'] and not e['visited'] 
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)
                select_succeeded = 1
        if select_succeeded == 0: 
            print('[%.2f] ERROR: All stations with docks had been visited -> Think about changing this par of the code' %
              (self.env.now))
            station_id=None
            station_location=None      
                
        station_location=np.array([lat,lon])
        return [station_id,station_location,visited_stations]

    def select_dockless_bike(self,location):

        values = []

        for bike in self.bikes:
            if isinstance(bike, DocklessBike):
                bike_id = bike.bike_id
                busy = bike.busy
                distance = self.dist(location, bike.location)
                walkable = distance < WALK_RADIUS
                lat=bike.location[0]
                lon=bike.location[1]
                values.append((bike_id, busy, distance, walkable,lat,lon))
        labels = ['bike_id', 'busy', 'distance', 'walkable','lat','lon']
        types = [int, int, float, int,float,float]
        dtype = list(zip(labels, types))
        bike_info = np.array(values, dtype=dtype)

        select_dockless_bike_succeeded = 0

        for e in np.sort(bike_info, order='distance'):
            valid = not e['busy'] and e['walkable']
            if valid:
                dockless_bike_id = e['bike_id']
                lat=e['lat']
                lon=e['lon']
                select_dockless_bike_succeeded = 1
                bike_location=np.array([lat,lon])
                break

        if select_dockless_bike_succeeded == 0:
            print('[%.2f] No bikes in walkable distance' %
              (self.env.now))
            dockless_bike_id=None
            bike_location=None

        return [dockless_bike_id,bike_location]

    def select_charging_station(self,location,visited_stations):
        values = []
        for station in self.charging_stations:
            station_id = station.station_id
            has_space = station.has_space()
            visited = station_id in visited_stations
            distance = self.dist(location, station.location) 
            lat=station.location[0]
            lon=station.location[1]
            values.append((station_id, has_space,
                           visited, distance,  lat, lon))
        labels = ['station_id', 'has_space',
                  'visited', 'distance', 'lat','lon'] 
        types = [int, int,
                 int, float, float, float] 
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        select_succeeded = 0

        for e in np.sort(station_info, order='distance'):
            valid = e['has_space'] and not e['visited']  
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)
                select_succeeded = 1  
                station_location=np.array([lat,lon]) 
                break         
  
        if select_succeeded == 0: 
            print('[%.2f] No charging stations with available space that have not been visited yet' %
              (self.env.now))
            station_id=None
            station_location=None

        return [station_id, station_location, visited_stations]

    def assign_autonomous_bike(self, location):
        values = []

        for bike in self.bikes:
            if isinstance(bike, AutonomousBike):
                bike_id = bike.bike_id
                busy = bike.busy
                distance = self.dist(location, bike.location)
                reachable = distance < MAX_AUTONOMOUS_RADIUS
                battery= bike.battery > MIN_BATTERY_LEVEL
                if battery == False and busy == False: #Otherwise it could be already on the way to chagring
                    bike.autonomous_charge()
                lat=bike.location[0]
                lon=bike.location[1]
                values.append((bike_id, busy, distance, reachable,battery, lat,lon))
        labels = ['bike_id', 'busy', 'distance', 'reachable', 'battery','lat','lon']
        types = [int, int, float, int, int, float,float]
        dtype = list(zip(labels, types))
        bike_info = np.array(values, dtype=dtype)

        select_autonomous_bike_succeeded = 0

        for e in np.sort(bike_info, order='distance'):
            valid = not e['busy'] and e['reachable'] and e[battery]
            if valid:
                autonomous_bike_id = e['bike_id']
                lat=e['lat']
                lon=e['lon']
                select_autonomous_bike_succeeded = 1
                bike_location=np.array([lat,lon])
                break

        if select_autonomous_bike_succeeded == 0:
            print("No autonomous bikes in "+ str(MAX_AUTONOMOUS_RADIUS) +" distance")
            autonomous_bike_id=None
            bike_location=None

        return [autonomous_bike_id,bike_location]


    def bike_ride(self, bike_id, location):
        bike=self.bikes[bike_id]
        yield self.env.process(bike.ride(location))
    def autonomous_bike_drive(self, bike_id, location):
        bike=self.bikes[bike_id]
        yield self.env.process(bike.autonomous_drive(location))

    def station_has_bikes(self, station_id):
        station=self.stations[station_id]
        valid=station.has_bikes()
        return valid
    # def station_n_bikes(self,station_id):
    #     station=self.stations[station_id]
    #     n_bikes=station.n_bikes()
    #     return n_bikes

    def station_has_docks(self, station_id):
        station=self.stations[station_id]
        valid=station.has_docks()
        return valid  
    # def station_n_docks(self,station_id):
    #     station=self.stations[station_id]
    #     n_docks=station.n_docks()
    #     return n_docks

    def charging_station_has_space(self,station_id):
        station=self.charging_stations[station_id]
        valid=station.has_space()
        return valid
    def station_choose_bike(self, station_id):
        station=self.stations[station_id]
        bike_id=station.choose_bike()
        return bike_id
    
    def station_attach_bike(self, station_id, bike_id):
        station=self.stations[station_id]
        station.attach_bike(bike_id)
    def station_detach_bike(self, station_id, bike_id):
        station=self.stations[station_id]
        station.detach_bike(bike_id)
    
    def charging_station_attach_bike(self,charging_station_id,bike_id):
        station=self.charging_stations[charging_station_id]
        station.attach_bike(bike_id)

    def charging_station_detach_bike(self,charging_station_id,bike_id):
        station=self.charging_stations[charging_station_id]
        station.detach_bike(bike_id)
    
    def bike_register_unlock(self, bike_id, user_id):
        bike=self.bikes[bike_id]
        bike.register_unlock(user_id)
    def bike_register_lock(self, bike_id, user_id):
        bike=self.bikes[bike_id]
        bike.register_lock(user_id)

    def dockless_bike_busy(self,dockless_bike_id):
        bike=self.bikes[dockless_bike_id]
        busy=bike.busy
        return busy
    def dockless_bike_unlock(self, dockless_bike_id, user_id):
        bike=self.bikes[dockless_bike_id]
        bike.unlock(user_id)
    def dockless_bike_lock(self,dockless_bike_id):
        bike=self.bikes[dockless_bike_id]
        bike.lock()

    def unlock_autonomous_bike(self, bike_id,user_id):
        bike=self.bikes[bike_id]
        bike.unlock(user_id)
    def bike_drop(self,bike_id):
        bike=self.bikes[bike_id]
        bike.drop()