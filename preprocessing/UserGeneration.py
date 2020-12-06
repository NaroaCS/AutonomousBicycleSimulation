#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 17:13:02 2020

@author: imartinez
"""
# %%
import numpy as np
import pandas as pd
import random

# %% IMPORT BUILDINGS 

import geopandas
df_buildings = geopandas.read_file("../data/buildings/buildings.shp")

df_buildings['cx'] = df_buildings.geometry.apply(lambda p: p.centroid.x)
df_buildings['cy'] = df_buildings.geometry.apply(lambda p: p.centroid.y)

lon_min = np.min(df_buildings['cx'])
lon_max = np.max(df_buildings['cx'])
lat_min = np.min(df_buildings['cy'])
lat_max = np.max(df_buildings['cy'])


# %% IMPORT TRIPS

df_trips = pd.read_csv('201910-bluebikes-tripdata.csv')
df_trips = df_trips[df_trips['start station longitude'].between(lon_min, lon_max) & 
                    df_trips['start station latitude'].between(lat_min, lat_max)]

# %%

from sklearn.neighbors import BallTree
tree = BallTree(np.deg2rad(df_buildings[['cx','cy']].values), leaf_size=10, metric="haversine") 

earth_radius = 6371000 # meters in earth
test_radius = 300 # meters
results = tree.query_radius(np.deg2rad(df_trips[['start station longitude', 'start station latitude']].values), 
                            r=test_radius/earth_radius, return_distance  = False)

df_trips['building'] = [np.random.choice(x) for x in results]
df_trips['start_lon'] = df_buildings['cx'][df_trips['building']].values
df_trips['start_lat'] = df_buildings['cy'][df_trips['building']].values

# include elapsed time
start_date = '2019-10-01 00:00:00'
start_time = pd.to_datetime(start_date)
df_trips['elapsed_time'] = (pd.to_datetime(df_trips['starttime']) - start_time).astype('timedelta64[s]')

df_trips.to_csv('output.csv')

# %% PLOT DATA 

plot = False
if plot:
    import matplotlib.pyplot as plt
    from pyproj import Proj
    pp = Proj("+proj=utm +zone=19 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

    df_stations = df_trips[['start station longitude', 'start station latitude']].drop_duplicates()
    df_trips_sample = df_trips.sample(100000)

    xx, yy = pp(df_trips_sample["start_lon"].values, df_trips_sample["start_lat"].values)
    df_trips_sample["X"] = xx
    df_trips_sample["Y"] = yy 

    xx, yy = pp(df_stations["start station longitude"].values, 
                df_stations["start station latitude"].values)
    df_stations["X"] = xx
    df_stations["Y"] = yy 


    plt.close('all')
    plt.figure(figsize=(16,9))
    plt.plot(df_stations['X'], df_stations['Y'], 
                color='black', marker='+', markersize=5, linestyle='None')
    plt.scatter(df_trips_sample['X'], df_trips_sample['Y'], 
                c=df_trips_sample['start station id'], s=1, cmap='rainbow', alpha=0.1)
    plt.axis('equal')
    plt.show()



