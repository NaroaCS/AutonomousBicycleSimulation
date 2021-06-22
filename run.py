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

MODE = 2
# %% PARAMETERS MODE 0

if MODE == 0:
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

# %% PARAMETERS MODE 1

if MODE == 1:
    config_path = os.path.join("data", "config_mode_1.json")
    with open(config_path) as f:
        config_nom = json.load(f)


    grid_x = {
        "NUM_BIKES": [2000,3000,4000,5000,6000,7000,8000,9000, 10000,11000]
    }
    grid_y = {
        "WALK_RADIUS": [100,300,500,750,1000,1500],
        "RIDING_SPEED": [5,8,10,12,15,20],
        "WALKING_SPEED": [3,4,5,6,7,8],
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

                    grid.append(config)

    pd.DataFrame(grid)


# %% PARAMETERS MODE 2

if MODE == 2:
    config_path = os.path.join("data", "config_mode_2_1.json")
    with open(config_path) as f:
        config_nom = json.load(f)


    grid_x = {
        "NUM_BIKES": [300,500,600,700,800,1000,1500,2000,2500,3000]
    }
    grid_y = {
        "AUTONOMOUS_RADIUS": [500,1000,1500,2000,2500,3000],
        "RIDING_SPEED": [5,8,10,12,15,20],
        #"WALKING_SPEED": [3,4,5,6,7,8],
        "AUTONOMOUS_SPEED": [1,2.5,5,10,15,20],
        "BATTERY_MIN_LEVEL": [5,10,15,20,25,30],
        "BATTERY_AUTONOMY": [30,50,70,90,110,130],
        "BATTERY_CHARGE_TIME": [0.5,1,2,4,6,8],
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

                    grid.append(config)

    pd.DataFrame(grid)


if MODE == 3:
    config_path = os.path.join("data", "config_mode_2.json")
    with open(config_path) as f:
        config_nom = json.load(f)

    grid_x = {
    "REBALANCING_EVERY": [-1, 15, 30, 45, 60, 120]
    }
    grid_y = {
    "REBALANCING_AHEAD": [0, 15, 30, 45, 60, 120],
    "REBALANCING_WINDOW": [15, 30, 45, 60, 120]
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

                    grid.append(config)

    pd.DataFrame(grid)

if MODE == 4:

    config_path = os.path.join("data", "config_mode_2.json")
    with open(config_path) as f:
        config_nom = json.load(f)

    grid_x = {
        "NUM_BIKES": [600,700,800,900,1000,1100]
    }
    grid_y = {
        "AUTONOMOUS_SPEED": [2.5,5,10,15]
    }
    grid_z = {
        #"AUTONOMOUS_RADIUS": [500,1000,1500,2000,2500,3000],
        #"RIDING_SPEED": [5,8,10,12,15,20],
        # "WALKING_SPEED": [3,4,5,6,7,8],
        #"BATTERY_MIN_LEVEL": [5,10,15,20,25,30],
        #"BATTERY_AUTONOMY": [30,50,70,90,110,130],
        #"BATTERY_CHARGE_TIME": [0.5,1,2,4,6,8],

    "REBALANCING_EVERY": [-1, 15, 30, 60, 120],
    "REBALANCING_AHEAD": [0, 15, 30, 60, 120],
    "REBALANCING_WINDOW": [15, 30, 60, 90, 120],

        #"USER_TRIPS_FILE": [0,1,2,3,4]
    }

    grid = []
    for kx in grid_x:
        for vx in grid_x[kx]:
            for ky in grid_y:
                for vy in grid_y[ky]:
                    for kz in grid_z:
                        for vz in grid_z[kz]:
                            # RESET CONFIG
                            config = config_nom.copy()
                            config[kx] = vx
                            config[ky] = vy    
                            config[kz] = vz

                            grid.append(config)

    print(pd.DataFrame(grid), len(grid))

if MODE == 5:

    config_path = os.path.join("data", "config_mode_2_predictive.json")
    with open(config_path) as f:
        config_nom = json.load(f)

    grid_x = {
        "NUM_BIKES": [600,800,1000,1250,1500,1750,2000,2500,3000]
    }
    grid_y = {
        "AUTONOMOUS_SPEED": [2.5,5,8,10,12,15,20]
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

                    grid.append(config)

    print(pd.DataFrame(grid), len(grid))




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
    city.run(until=750000)
    # city.run(until=650)
    print("[", k, "/", len(grid) ,"]", round(time.time() - start, 3))
    #break

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
