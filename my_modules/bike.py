import simpy 
#import random 
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
from my_modules.Router import Network
#import time

network=Network()
RIDING_SPEED = 15/3.6 #m/s
AUT_DRIVING_SPEED = 10/3.6 #m/s
BATTERY_CONSUMPTION_METER= 0.1 #Just a random number for now
CHARGING_SPEED= 100/(0.0005*3600) #%/second  (This is 5h for 100% charge)

class Bike:
    def __init__(self,env, bike_id):
        self.env=env
        self.bike_id=bike_id
        self.location=None
        self.user=None
        self.busy=False #reserved, driving autonomously, in use...

    def set_location(self, lat, lon):
        self.location = np.array([lat,lon])
    
    def update_user(self,user_id):
        self.user = user_id

    def delete_user(self):
        self.user = None

    def vacant(self):
        if (self.user is None):
            return True

    def ride(self,destination):
        distance = self.dist(self.location, destination)
        time=distance/RIDING_SPEED
        yield self.env.timeout(time)
        self.location = destination

    def dist(self, a, b):
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

    def unlock(self, user_id):
        self.update_user(user_id)
        self.busy=True

    def lock(self):
        self.delete_user()
        self.busy=False

class AutonomousBike(Bike):
    def __init__(self,env, bike_id,datainterface):
        super().__init__(env, bike_id)
        self.datainterface=datainterface
        self.battery= 26 #We will assume that all the bikes start with a full charge
        self.charging_station_id = None
        self.visited_stations=[]

    def go_towards(self, destination_location): #This is for the demand prediction -> maybe it's enugh with autonomous_drive()  
        distance = self.dist(self.location, destination_location) 
        time=distance/AUT_DRIVING_SPEED
        yield self.env.timeout(time)
        self.location = destination_location

    def autonomous_drive(self, user_location):
        print('[%.2f] Bike %d driving autonomously from [%.4f, %.4f] to location [%.4f, %.4f]' % (self.env.now, self.bike_id, self.location[0], self.location[1], user_location[0], user_location[1]))
        distance = self.dist(self.location, user_location)
        time=distance/AUT_DRIVING_SPEED
        yield self.env.timeout(time)
        self.location =user_location
        self.battery= self.battery-distance*BATTERY_CONSUMPTION_METER
        print('[%.2f] Battery level of bike %d: %.2f' % (self.env.now, self.bike_id,self.battery))
        print('[%.2f] Bike %d drove autonomously from [%.4f, %.4f] to location [%.4f, %.4f]' % (self.env.now, self.bike_id, self.location[0], self.location[1], user_location[0], user_location[1]))

    def drop(self):
        self.delete_user()
        self.busy=False

    def unlock(self, user_id):
        self.update_user(user_id)
        self.busy=True
        
    def autonomous_charge(self): #Triggered when battery is below a certain SOC
        print('autonomous_charge')
        self.env.process(self.process())   

    def process(self):

        print('[%.2f] Bike %d needs to recharge. Battery level:  %.2f' % (self.env.now, self.bike_id,self.battery))
        #Set bike as busy
        self.busy=True
        self.event_interact_chargingstation = self.env.event()

        while not self.event_interact_chargingstation.triggered:
            #Select charging station
            [station,station_location,visited_stations]=self.select_charging_station(self.location,self.visited_stations)
            self.charging_station_id=station

            if self.charging_station_id is None:
                continue #Will try again

            print('[%.2f] Bike %d going to station %d for recharge' % (self.env.now, self.bike_id, self.charging_station_id))

            #Drive autonomously to station
            yield self.env.process(self.autonomous_drive(station_location))

            #Lock in station
            yield self.env.process(self.interact_charging_station(action='lock'))

            charging_start_time=self.env.now
        print('[%.2f] Bike %d started recharging' % (self.env.now, self.bike_id))
        self.event_interact_chargingstation=self.env.event()

        #wait until it charges
        yield self.env.process(self.charging())  

        #Leave station (unlock and not busy)
        yield self.env.process(self.interact_charging_station(action='unlock'))

        #Bike is free for use again
        self.busy=False
        print('[%.2f] Bike %d is charged and available again' % (self.env.now, self.bike_id))

    def select_charging_station(self, location, visited_stations):
        selected_station_info=self.datainterface.select_charging_station(location,visited_stations) 
        return selected_station_info

    def interact_charging_station(self,action):
        charging_station_id=self.charging_station_id
        if action=='lock':
            #check if there are available bikes
            valid = self.datainterface.charging_station_has_space(charging_station_id)
            if valid:
                self.datainterface.charging_station_attach_bike(charging_station_id,self.bike_id)
                self.event_interact_chargingstation.succeed()
            else:
                print('[%.2f] Charging station %d had zero spaces available at arrival' %
                (self.env.now, self.station_id))
        else: #unlock
            self.datainterface.charging_station_detach_bike(charging_station_id,self.bike_id)
            self.event_interact_chargingstation.succeed()
        
        yield self.env.timeout(1)

    def charging(self):
        charging_time=(100-self.battery)/CHARGING_SPEED
        yield self.env.timeout(charging_time)
        self.battery=100
