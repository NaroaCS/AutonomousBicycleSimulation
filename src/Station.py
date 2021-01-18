import simpy
import random
import numpy as np
import pandas as pd


class Station:
    id_count = -1

    def __init__(self, env):
        self.next_id()
        self.id = Station.id_count

        self.env = env  # TODO: NEEDS ACCESS TO ENVIRONMENT ???
        self.location = None
        self.capacity = 0
        self.num_bikes = 0
        self.bikes = []

    def next_id(self):
        Station.id_count += 1

    def set_location(self, location):
        self.location = location

    def set_capacity(self, capacity):
        self.capacity = capacity

    def has_bikes(self):
        return self.num_bikes > 0

    def has_docks(self):
        return self.capacity - self.num_bikes > 0

    def empty(self):
        return self.num_bikes == 0

    def full(self):
        return self.num_bikes == self.capacity

    def choose_bike(self):  # Selects any bike
        return random.choice(self.bikes)

    def attach_bike(self, bike_id):  # What happens if no docks?
        if self.has_docks():
            self.bikes.append(bike_id)
            self.num_bikes += 1
            return True
        else:
            print("[%.2f] Station %d has no docks available" % (self.env.now, self.station_id))
            return False

    def detach_bike(self, bike_id):  # What happens if no bikes?
        if self.has_bikes():
            # bike_id=random.choice(self.bikes)
            self.bikes.remove(bike_id)
            self.num_bikes -= 1
            return True
        else:
            print("[%.2f] Station %d has no bikes available" % (self.env.now, self.station_id))
            return False
