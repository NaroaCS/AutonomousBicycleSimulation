import simpy 
import random 
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
#from Router import Network
#import time

class ChargingStation:
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

    def has_space(self):
        return self.capacity - self.n_bikes > 0

    def attach_bike(self, bike_id): #What hapens if no docks?
        if self.has_space(): 
            self.n_bikes+=1 
            self.bikes.append(bike_id) 
        else:
            print('[%.2f] Charging station %d has no spaces available' %
              (self.env.now, self.station_id))

    def detach_bike(self, bike_id): 
        self.n_bikes-=1 
        self.bikes.remove(bike_id) 