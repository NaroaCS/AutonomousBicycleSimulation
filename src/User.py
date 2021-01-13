import simpy 
import random 
import numpy as np
import pandas as pd
import json

#from .Router import Network
from .Graph import Graph
from .Location import Location

#network=Graph()

with open('config.json') as config_file:
    params = json.load(config_file)

WALKING_SPEED= params['WALKING_SPEED']/3.6 #m/s
BETA= params['BETA']  #probability of getting a magic bike or dock in %

class User:
    def __init__(self,env, network, user_id, origin, destination, departure_time):
        self.env=env
        self.user_id=user_id
        self.location= None
        self.state=None #None, walking,waiting,biking ..> Not used for now
        self.event_setup_task = self.env.event() # ?¿ Here or in a start() function
        self.bike_id=None

        self.origin=origin
        self.destination=destination
        self.departure_time=departure_time

        self.network = network
    
    def process(self):

        # 1-Init on origin
        yield self.env.process(self.init_user())

    def init_user(self):
        #waits until its the hour to initialize user
        yield self.env.timeout(self.departure_time) 
        self.location = self.origin
        print('[%.2f] User %d initialized at location [%.4f, %.4f]' % (self.env.now, self.user_id, self.location[0], self.location[1]))
                  
    def walk_to(self, location):
        distance = self.dist(self.location, location)
        time=distance/WALKING_SPEED
        yield self.env.timeout(time)
        print('[%.2f] User %d walked from [%.4f, %.4f] to location [%.4f, %.4f]' % (self.env.now, self.user_id, self.location[0], self.location[1], location[0], location[1]))
        self.location = location

    def ride_bike_to(self, location):
        bike_id=self.bike_id
        print('[%.2f] User %d biking from [%.4f, %.4f] to location [%.4f, %.4f]' % (self.env.now, self.user_id, self.location[0], self.location[1], location[0], location[1]))
        yield self.env.process(self.datainterface.bike_ride(bike_id, location)) 
        self.location = location
        
    
    def dist(self, a, b):
        a = Location(a[1], a[0])
        b = Location(b[1], b[0])
        d = self.network.get_shortest_path_length(a,b)
        return d

class StationBasedUser(User):
    def __init__(self, env, network, user_id, origin, destination, departure_time, datainterface):
        super().__init__(env, network, user_id, origin, destination, departure_time)
        self.datainterface=datainterface
        #self.rebalancingmanager=rebalancingmanager

    def start(self):   
        self.station_id = None
        self.event_select_station = self.env.event()
        self.event_interact_bike = self.env.event()
        self.visited_stations = []

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

            if self.station_id is None:
                rand_number= random.randint(1,100)
                if rand_number <= BETA:
                    print('[%.2f] User %d  made a magic bike request' % (self.env.now, self.user_id))
                    [station, station_location, visited_stations]= self.datainterface.magic_bike(self.location, self.visited_stations)
                    self.station_id=station
                    if station is None:
                        print('[%.2f] User %d  will not make the trip' % (self.env.now, self.user_id))
                        return
                elif rand_number > BETA:
                    print('[%.2f] User %d  will not make the trip' % (self.env.now, self.user_id))
                    return
            ### HOW DO WE SAVE THE MAGIC BIKES ???? ###


            print('[%.2f] User %d selected start station [%.4f, %.4f]' % (self.env.now, self.user_id, station_location[0],station_location[1]))


            # 3-Walk to origin station
            yield self.env.process(self.walk_to(station_location))

            # 4-unlock bike
            yield self.env.process(self.interact_bike(action='unlock'))
            
        self.event_interact_bike = self.env.event()
        visited_stations.clear() #here we should zero it because one might do a round trip
        
        while not self.event_interact_bike.triggered:
            # 5-Select destination station
            [station, station_location, visited_stations]=self.select_end_station(self.destination,self.visited_stations)
            self.station_id=station

            

            if self.station_id is None:
                rand_number= random.randint(1,100)
                if rand_number <= BETA:
                    print('[%.2f] User %d  made a magic dock request' % (self.env.now, self.user_id))
                    [station, station_location, visited_stations]= self.datainterface.magic_dock(self.location, self.visited_stations)
                    if station is None:
                        print('[%.2f] User %d  will end at a station out of walkable distance' % (self.env.now, self.user_id))
                        [station, station_location, visited_stations]= self.datainterface.notwalkable_dock(self.location, self.visited_stations)
                    
                elif rand_number > BETA:
                    print('[%.2f] User %d  will end at a station out of walkable distance' % (self.env.now, self.user_id))
                    [station, station_location, visited_stations]= self.datainterface.notwalkable_dock(self.location, self.visited_stations)

            ### HOW DO WE SAVE THE MAGIC docks???? ###
            
            self.station_id=station
            print('[%.2f] User %d selected end station %d' % (self.env.now, self.user_id, self.station_id))

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
        print('[%.2f] User %d arrived to final destination' % (self.env.now, self.user_id))
    
    def select_start_station(self,location,visited_stations):
        selected_station_info=self.datainterface.select_start_station(location,visited_stations)
        return selected_station_info

    def select_end_station(self,destination,visited_stations):
        selected_station_info=self.datainterface.select_end_station(destination,visited_stations)
        return selected_station_info


    def interact_bike(self, action):
        station_id=self.station_id
        
        #Check if there are still bikes(unlock)/docks(lock) at arrival
        if action=='unlock':
            valid=self.datainterface.station_has_bikes(station_id)
        else: #lock
            valid=self.datainterface.station_has_docks(station_id)
    
        if valid:
            if action == 'unlock':
                self.bike_id = self.datainterface.station_choose_bike(station_id)
                bike_id=self.bike_id
                self.datainterface.bike_register_unlock(bike_id, self.user_id)
                self.datainterface.station_detach_bike(station_id, bike_id)
            else: #lock
                bike_id=self.bike_id
                self.datainterface.bike_register_lock(bike_id, self.user_id)
                self.datainterface.station_attach_bike(station_id, self.bike_id)

            self.event_interact_bike.succeed()

            yield self.env.timeout(1)

        else: 
            print('[%.2f] Station %d had zero %s available at arrival' %
                       (self.env.now, self.station_id, 'bikes' if action == 'unlock' else 'docks'))
             
class DocklessUser(User):
    def __init__(self, env, network, user_id, origin, destination, departure_time, datainterface):
        super().__init__(env, network, user_id, origin, destination, departure_time)
        self.datainterface=datainterface
    def start(self):
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

            if dockless_bike_id is None:
                print('[%.2f] User %d  will not make the trip' % (self.env.now, self.user_id))
                return

            print('[%.2f] User %d selected dockless bike %d' % (self.env.now, self.user_id, dockless_bike_id))

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
        print('[%.2f] User %d arrived to final destination' % (self.env.now, self.user_id))
           
    def select_dockless_bike(self,location):

        selected_bike_info=self.datainterface.select_dockless_bike(location)
        return selected_bike_info

    def unlock_bike(self):
        dockless_bike_id=self.bike_id
        if not self.datainterface.dockless_bike_busy(dockless_bike_id):
            yield self.env.timeout(1)
            self.bike_id = dockless_bike_id
            self.datainterface.dockless_bike_unlock(dockless_bike_id, self.user_id)
            self.event_unlock_bike.succeed()
        else:
            yield self.env.timeout(3)
            print('[%.2f] User %d -> Bike %d has already been rented. Looking for another one.' % (self.env.now, self.user_id,dockless_bike_id))

    def lock_bike(self):
        dockless_bike_id=self.bike_id
        self.datainterface.dockless_bike_lock(dockless_bike_id)

class AutonomousUser(User):
    def __init__(self, env, network, user_id, origin, destination, departure_time, datainterface):
        super().__init__(env, network, user_id, origin, destination, departure_time)
        #self.demandmanager=demandmanager
        self.datainterface=datainterface

    def start(self):
        self.event_call_autonomous_bike = self.env.event()
        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on origin
        yield self.env.process(super().process())

        # 2-Call autonomous bike
        [autonomous_bike_id,autonomous_bike_location]=self.call_autonomous_bike(self.location)
        self.bike_id=autonomous_bike_id

        if self.bike_id is None:
            print('[%.2f] User %d  will not make the trip' % (self.env.now, self.user_id))
            return

        print('[%.2f] User %d was assigned the autonomous bike %d' % (self.env.now, self.user_id, autonomous_bike_id))
       

        # 3-Wait for autonomous bike
        yield self.env.process(self.drive_autonomously())
        self.datainterface.unlock_autonomous_bike(self.bike_id,self.user_id)

        # 4-Ride bike
        yield self.env.process(self.ride_bike_to(self.destination))

        # 5-Drop bike
        self.drop_bike()
        print('[%.2f] User %d dropped the autonomous bike %d at the destination [%.4f, %.4f]' % (self.env.now, self.user_id, autonomous_bike_id, self.location[0],self.location[1]))

        # 6-Save state
        #self.save_state()

        # 7-Finish
        yield self.env.timeout(10)
        print('[%.2f] User %d arrived to final destination' % (self.env.now, self.user_id))

    def drive_autonomously(self):
        yield self.env.process(self.datainterface.autonomous_bike_drive(self.bike_id, self.location))

    def call_autonomous_bike(self, location):  
        assigned_bike_info=self.datainterface.assign_autonomous_bike(location)
        return assigned_bike_info

    def drop_bike(self):
        #bike = self.bikes[self.bike_id]
        bike_id=self.bike_id
        self.datainterface.bike_drop(bike_id)