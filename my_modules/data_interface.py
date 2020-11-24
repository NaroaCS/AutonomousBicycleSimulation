import simpy 
#import random 
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
from my_modules.Router import Network
#import time

from my_modules.bike import Bike, StationBike, DocklessBike, AutonomousBike
from my_modules.user import User, StationBasedUser, DocklessUser, AutonomousUser

network=Network()

WALK_RADIUS = 3500 #Just to try the dockless mode !
MAX_AUTONOMOUS_RADIUS= 3000


class DataInterface:

    def __init__(self,env):
        self.env=env

    def set_data(self, stations, charging_stations, bikes):
        self.stations = stations
        self.bikes = bikes
        self.charging_stations= charging_stations

    def dist(self, a, b):
        route=network.get_route(a[1], a[0], b[1], b[0])
        d=route['cum_distances'][-1]
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
            print('[%.2f] No bikes fount in a walkable distance' %
              (self.env.now))
            station_id=None
            station_location=None

        return [station_id, station_location, visited_stations] 

    def select_end_station(self,destination,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_docks = station.has_docks()
            visited = station_id in visited_stations
            distance = self.dist(destination, station.location) 
            walkable = distance < WALK_RADIUS # ---> Once that ou're in the bike you have to leav eit even if it's very far
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
                if not e['walkable']:
                    print('[%.2f] (Note) The station slected is located ot of a walkable distance from the destination' %
                    (self.env.now))
                break        
                
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
    def station_has_docks(self, station_id):
        station=self.stations[station_id]
        valid=station.has_docks()
        return valid  
    
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
    def station_detach_bike(self, station_id):
        station=self.stations[station_id]
        station.detach_bike()
    
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