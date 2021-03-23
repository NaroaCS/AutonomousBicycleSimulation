# %% IMPORT MODULES
import json
import pandas as pd
import numpy as np
import time
import os

from src.SimulationEngine import SimulationEngine
from preprocessing.BikeGeneration import BikeGeneration
from src.Graph import Graph

# %% LOAD GRAPH

name = "greater_boston_road"
name = "greater_boston_walk"
# graph = Graph(name)
# graph.save()

graph = Graph.load(name)

# %% PARAMETERS

config_path = os.path.join("data", "config_mode_0.json")
with open(config_path) as f:
    config_nom = json.load(f)


grid_x = {
    "NUM_BIKES": [1000,1500,2000,2500,3000,3500,4000,4500,5000,5500]
}
grid_y = {
    "WALK_RADIUS": [100,300,500,750,1000,1500],
    "RIDING_SPEED": [5,8,10,12,15,20],
    "WALKING_SPEED": [3,4,5,6,7,8],
    "MAGIC_BETA": [0,50,80,90,98,100],
    "MAGIC_MIN_BIKES": [0,1,2,3,4,5],
    "USER_TRIPS_FILE": [0,1,2,3,4]
}


grid = []
for kx in grid_x:
    for vx in grid_x[kx]:
        for ky in grid_y:
            for vy in grid_y[ky]:
                # RESET CONFIG
                config = config_nom.copy()
                config[kx] = vx
                config[ky] = vy
                
                # minor fix for station based
                config["MAGIC_MIN_DOCKS"] = config["MAGIC_MIN_BIKES"]      

                grid.append(config)

pd.DataFrame(grid)

# %% RUN MULTIPLE SIMULATIONS

k = 0
for config in grid:
    k += 1
    users_path = os.path.join("data", "user_trips_"+ str(config["USER_TRIPS_FILE"]) +".csv")

    stations_path = os.path.join("data", "bluebikes_stations_07_2020.csv")
    stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
    users_data = pd.read_csv(users_path) #, nrows=2000)

    start = time.time()
    city = SimulationEngine(config, stations_data, users_data, graph)
    city.run(until=650000)
    # city.run(until=650)
    print("[", k, "/", len(grid) ,"]", round(time.time() - start, 3))
    break

# %% RUN ONE SIMULATION (EXAMPLE)

if False:
    from src.SimulationEngine import SimulationEngine
    from preprocessing.BikeGeneration import BikeGeneration

    config_path = os.path.join("data", "config_mode_0.json")
    stations_path = os.path.join("data", "bluebikes_stations_07_2020.csv")
    users_path = os.path.join("data", "user_trips_0.csv")

    with open(config_path) as f:
        config = json.load(f)

    stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
    users_data = pd.read_csv(users_path, nrows=2000)

    start = time.time()
    city = SimulationEngine(config, stations_data, users_data, graph)
    city.run(until=650000)
    print(i, time.time() - start)
