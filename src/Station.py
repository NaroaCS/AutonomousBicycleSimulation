import simpy 
import random 
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
#from Router import Network
#import time


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

    def attach_bike(self, bike_id): #What hapens if no docks?
        if self.has_docks(): 
            self.n_bikes+=1 
            self.bikes.append(bike_id) 
        else:
            print('[%.2f] Station %d has no docks available' %
              (self.env.now, self.station_id))

    def detach_bike(self): #What hapens if no bikes?
        if self.has_bikes(): 
            self.n_bikes-=1 
            bike_id=random.choice(self.bikes) 
            self.bikes.remove(bike_id) 
        else:
            print('[%.2f] Station %d has no bikes available' %
              (self.env.now, self.station_id))