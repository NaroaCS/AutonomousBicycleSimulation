import json
import pandas as pd
import time
import logging
import os
import datetime

cwd = os.getcwd()
now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
path = os.path.join(cwd, 'results', now)
os.mkdir(path)


logging.basicConfig(filename="./app.log", filemode="w", format="%(levelname)s:%(message)s", level=logging.INFO)

from src.SimulationEngine import SimulationEngine
from preprocessing.BikeGeneration import BikeGeneration

config_path = os.path.join(cwd, "data", "config.json")
stations_path = os.path.join(cwd, "data", "bluebikes_stations_07_2020.csv")
users_path = os.path.join(cwd, "data", "user_trips.csv")

with open(config_path) as f:
    config = json.load(f)

stations_data = BikeGeneration(config["NUM_BIKES"], config["MODE"], stations_path)
users_data = pd.read_csv(users_path, nrows=200)  # .tail(2)  # .head(200).sample(random_state=0)

city = SimulationEngine(config, stations_data, users_data)
city.save_config(path)

start = time.time()
city.run(until=150000)
print(time.time() - start)
