# LIBRARIES
import simpy
import numpy as np
import pandas as pd
import logging
import json
import os

# CLASSES
from .Station import Station

from .BikeStation import BikeStation
from .BikeDockless import BikeDockless
from .BikeAutonomous import BikeAutonomous

from .UserStation import UserStation
from .UserDockless import UserDockless
from .UserAutonomous import UserAutonomous

from .DataInterface import DataInterface
from .Location import Location
from .Graph import Graph
from .EnergyManager import EnergyManager
from .Results import Results


class SimulationEngine:
    def __init__(self, config, stations_data, users_data):
        self.config = config
        self.stations_data = stations_data
        self.users_data = users_data

        self.env = simpy.Environment()
        self.graph = Graph()
        self.ui = DataInterface(self.env, self.graph, self.config)
        self.charger = EnergyManager(self.env, self.config)
        self.results = Results(self.config)

        self.stations = []
        self.bikes = []
        self.users = []

        self.MODE = self.config["MODE"]  # 0 for StationBased / 1 for Dockless / 2 for Autonomous
        self.NUM_BIKES = self.config["NUM_BIKES"]

        self.start()

    def run(self, until):
        print("Simulation Started")
        self.env.run(until)
        print("Simulation Finished")

    def start(self):
        if self.MODE != 1:
            self.init_stations()
        self.init_bikes()
        self.init_managers()
        self.init_users()

    def init_stations(self):
        nodes = self.stations_data[["Longitude", "Latitude"]].values
        self.stations_data["Node"] = self.graph.precompute_stations_nodes(nodes)  # precompute closest graph nodes to each station
        for _, station in self.stations_data.iterrows():
            s = Station(self.env)
            s.set_capacity(station["Docks"])
            s.set_location(Location(station["Longitude"], station["Latitude"], station["Node"]))
            self.stations.append(s)

        self.graph.create_kdtree_stations(nodes)  # create kdtree for stations

        maxdist = 2000
        maxitems = 20
        self.graph.precompute_nearest_stations(nodes, maxdist, maxitems)  # set poi-s

    def init_bikes(self):
        if self.MODE == 0:
            for station_id, station in self.stations_data.iterrows():
                for i in range(station["Bikes"]):
                    bike = BikeStation(self.env, self.graph, self.config)
                    bike.attach_station(station_id)  # saves the station in the bike
                    bike.set_location(self.stations[station_id].location)
                    self.stations[station_id].attach_bike(bike.id)  # saves the bike in the station
                    self.bikes.append(bike)
        elif self.MODE == 1:
            for station_id, station in self.stations_data.iterrows():  # TODO: review bike generation
                for i in range(station["Bikes"]):
                    bike = BikeDockless(self.env, self.graph, self.config)
                    location = Location(station["Longitude"], station["Latitude"])
                    bike.set_location(location)
                    self.bikes.append(bike)
        elif self.MODE == 2:
            for station_id, station in self.stations_data.iterrows():  # TODO: review bike generation
                for i in range(station["Bikes"]):
                    bike = BikeAutonomous(self.env, self.graph, self.config, self.ui, self.results)
                    location = Location(station["Longitude"], station["Latitude"])
                    bike.set_location(location)
                    self.bikes.append(bike)

    def init_users(self):
        self.users_data["start_node"] = self.graph.network.get_node_ids(self.users_data["start_lon"], self.users_data["start_lat"])
        self.users_data["target_node"] = self.graph.network.get_node_ids(self.users_data["target_lon"], self.users_data["target_lat"])

        print("Loading users")
        for _, trip in self.users_data.iterrows():
            origin = Location(trip["start_lon"], trip["start_lat"], trip["start_node"])
            destination = Location(trip["target_lon"], trip["target_lat"], trip["target_node"])
            departure_time = trip["start_time"]  # / 60  # departure time
            target_time = trip["target_time"]  # target time
            if self.MODE == 0:
                user = UserStation(self.env, self.graph, self.ui, self.config, self.results, origin, destination, departure_time, target_time)
            elif self.MODE == 1:
                user = UserDockless(self.env, self.graph, self.ui, self.config, self.results, origin, destination, departure_time, target_time)
            elif self.MODE == 2:
                user = UserAutonomous(self.env, self.graph, self.ui, self.config, self.results, origin, destination, departure_time, target_time)
            user.start()
            self.users.append(user)

    def init_managers(self):
        if self.MODE != 1:
            self.ui.set_stations(self.stations)
        self.ui.set_bikes(self.bikes)

        if self.MODE == 2:
            self.charger.set_bikes(self.bikes)
            # self.charger.start()
