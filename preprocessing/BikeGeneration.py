import json
import pandas as pd
import numpy as np

import os
import sys
os.chdir(os.path.dirname(sys.argv[0]))

# stations_data = pd.read_csv('../data/bluebikes_stations_01_2021.csv')
stations_data = pd.read_csv('../data/bluebikes_stations_07_2020.csv')
stations_data = stations_data.rename(columns={'Total docks': "Docks"})
stations_data = stations_data[stations_data['Docks'] > 0].reset_index(drop=True)
num_stations = len(stations_data)
num_docks = stations_data['Docks'].sum()

with open('../data/config.json') as config_file:
    params = json.load(config_file)

num_bikes = min(params['NUM_BIKES'], num_docks)

count = 0
stations_data['Bikes'] = 0
stations_data['prob'] = stations_data['Docks'] / num_docks
while count < num_bikes:
  station_id = np.random.choice(num_stations, size=None, replace=False, p=stations_data['prob'])
  stations_data.loc[station_id, 'Bikes'] += 1
  count += 1
  stations_data['prob'] = (stations_data['Docks']-stations_data['Bikes']) / (num_docks - count)
  
# stations_data['Bikes'] = np.floor(stations_data['Total docks'] * num_bikes / num_docks).astype(int)
stations_data = stations_data.drop(columns=['prob'], axis=1)
stations_data.to_csv('../data/bluebikes_stations_bikes.csv', index=False)
