import json
import pandas as pd
import time
import os

from src.SimulationEngine import SimulationEngine
from preprocessing.BikeGeneration import BikeGeneration

config_path = os.path.join("data", "config.json")

with open(config_path) as f:
    config = json.load(f)

stations_path = os.path.join("data", "bluebikes_stations_07_2020.csv")
users_path = os.path.join("data", "user_trips_"+ str(config["USER_TRIPS_FILE"]) +".csv")
#users_path = os.path.join("data", "user_trips_0.csv")



stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
users_data = pd.read_csv(users_path)

city = SimulationEngine(config, stations_data, users_data)

start = time.time()
city.run(until=1300000)
print(time.time() - start)
