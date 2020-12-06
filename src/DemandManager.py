import simpy 
#import random 
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
from .Router import Network
#import time

from .Bike import Bike, AutonomousBike

network=Network()
MAX_AUTONOMOUS_RADIUS= 3000
MIN_BATTERY_LEVEL= 25

class DemandManager:
    #receives orders from users and decides which bike goes
    def __init__(self,env):
        self.env=env
    
    def set_data(self, bikes):
        self.bikes = bikes

    def dist(self, a, b):
        route=network.get_route(a[1], a[0], b[1], b[0])
        d=route['cum_distances'][-1]
        return d
      

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