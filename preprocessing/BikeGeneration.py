import pandas as pd
import numpy as np

def BikeGeneration(num_bikes, mode, stations_csv):
    print("Generating Bikes")
    stations_data = pd.read_csv(stations_csv)
    stations_data = stations_data.rename(columns={'Total docks': "Docks"})
    stations_data = stations_data[stations_data['Docks'] > 0].reset_index(drop=True)
    num_stations = len(stations_data)
    num_docks = stations_data['Docks'].sum()

    if mode == 0:
        num_bikes = min(num_bikes, num_docks) 

    count = 0
    stations_data['Bikes'] = 0
    stations_data['prob'] = stations_data['Docks'] / num_docks
    while count < num_bikes:
        station_id = np.random.choice(num_stations, size=None, replace=False, p=stations_data['prob'])
        stations_data.loc[station_id, 'Bikes'] += 1
        count += 1
        stations_data['prob'] = (stations_data['Docks']-stations_data['Bikes']) / (num_docks - count)

    stations_data = stations_data.drop(columns=['prob'], axis=1)
    # stations_data['Bikes'] = np.floor(stations_data['Total docks'] * num_bikes / num_docks).astype(int)
    # stations_data.to_csv('../data/bluebikes_stations_bikes.csv', index=False)
    return stations_data
