# %% IMPORT MODULES
import json
import pandas as pd
import time
import os

# %% LOAD GRAPH
from src.Graph import Graph

name = "greater_boston_road"
# name = "greater_boston_walk"
# graph = Graph(name)
# graph.save()

graph = Graph.load(name)

# %% LOAD

from src.SimulationEngine import SimulationEngine
from preprocessing.BikeGeneration import BikeGeneration

config_path = os.path.join("data", "config_mode_0.json")
stations_path = os.path.join("data", "bluebikes_stations_07_2020.csv")
users_path = os.path.join("data", "user_trips.csv")

with open(config_path) as f:
    config = json.load(f)

stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
users_data = pd.read_csv(users_path, nrows=2000)

for i in range(2):
    start = time.time()
    city = SimulationEngine(config, stations_data, users_data, graph)
    city.run(until=650000)
    print(i, time.time() - start)
