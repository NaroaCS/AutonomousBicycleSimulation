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

df_buildings["cx"] = df_buildings.geometry.apply(lambda p: p.centroid.x)
df_buildings["cy"] = df_buildings.geometry.apply(lambda p: p.centroid.y)

lon_min = np.min(df_buildings["cx"])
lon_max = np.max(df_buildings["cx"])
lat_min = np.min(df_buildings["cy"])
lat_max = np.max(df_buildings["cy"])


# %% IMPORT TRIPS

df_trips = pd.read_csv("../data/201910-bluebikes-tripdata.csv")

# DATE FILTER
start_date = "2019-10-14 00:00:00"
end_date = "2019-10-20 00:00:00"
df_trips = df_trips[df_trips["starttime"].between(start_date, end_date)]

# ROUNDTRIP FILTER
df_trips = df_trips[df_trips["start station id"] != df_trips["end station id"]]

# LOCATION FILTER
df_trips = df_trips[
    df_trips["start station longitude"].between(lon_min, lon_max) & 
    df_trips["start station latitude"].between(lat_min, lat_max)]

print(len(df_trips))

# %%

from sklearn.neighbors import BallTree

tree = BallTree(np.deg2rad(df_buildings[["cy", "cx"]].values), leaf_size=50, metric="haversine")

earth_radius = 6378137.0  # meters in earth
test_radius = 300.0  # meters

# Example
if False:
    import matplotlib.pyplot as plt

    lon0 = -71.113054
    lat0 = 42.372509
    results = tree.query_radius(np.radians(np.array([[lat0, lon0]])), 
        r=test_radius / earth_radius, return_distance=False,)
    a = df_buildings.loc[results[0], ["cx", "cy"]]
    plt.figure()
    plt.scatter(a["cx"], a["cy"])
    plt.axis("equal")

    def merc(lon, lat):
        r_major = 6378137.0
        x = r_major * np.radians(lon)
        scale = x / lon
        y = 180.0 / np.pi * np.log(np.tan(np.pi / 4.0 + lat * (np.pi / 180.0) / 2.0)) * scale
        return x, y

    def haversine(s_lat, s_lng, e_lat, e_lng):
        # approximate radius of earth in meters
        R = 6378137.0

        s_lat = s_lat * np.pi / 180.0
        s_lng = np.deg2rad(s_lng)
        e_lat = np.deg2rad(e_lat)
        e_lng = np.deg2rad(e_lng)

        d = np.sin((e_lat - s_lat) / 2) ** 2 + np.cos(s_lat) * np.cos(e_lat) * np.sin((e_lng - s_lng) / 2) ** 2

        return 2 * R * np.arcsin(np.sqrt(d))

    plt.figure()
    plt.hist(haversine(lat0, lon0, a["cy"], a["cx"]))

    plt.figure()
    x, y = merc(a["cx"], a["cy"])
    plt.scatter(x, y)
    plt.axis("equal")

    x0, y0 = merc(lon0, lat0)
    plt.figure()
    plt.hist(np.sqrt((x - x0) ** 2 + (y - y0) ** 2))


# start locations
results_start = tree.query_radius(np.deg2rad(df_trips[["start station latitude", "start station longitude"]].values), 
    r=test_radius / earth_radius, return_distance=False,)

df_trips["start_building"] = [np.random.choice(x) for x in results_start]
df_trips["start_lon"] = df_buildings["cx"][df_trips["start_building"]].values
df_trips["start_lat"] = df_buildings["cy"][df_trips["start_building"]].values

# target locations
results_target = tree.query_radius(np.deg2rad(df_trips[["end station latitude", "end station longitude"]].values), 
    r=test_radius / earth_radius, return_distance=False,)

df_trips["target_building"] = [np.random.choice(x) for x in results_target]
df_trips["target_lon"] = df_buildings["cx"][df_trips["target_building"]].values
df_trips["target_lat"] = df_buildings["cy"][df_trips["target_building"]].values


# include elapsed time
start_time = pd.to_datetime(start_date)
df_trips["start_time"] = (pd.to_datetime(df_trips["starttime"]) - start_time).astype("timedelta64[s]")
df_trips["target_time"] = (pd.to_datetime(df_trips["stoptime"]) - start_time).astype("timedelta64[s]")

# df_trips.drop(columns = [])
df_trips.to_csv("../data/user_trips.csv", index=False)

# %% PLOT DATA

plot = False
if plot:
    import matplotlib.pyplot as plt
    from pyproj import Proj

    pp = Proj("+proj=utm +zone=19 +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

    df_stations = df_trips[["start station longitude", "start station latitude"]].drop_duplicates()
    df_trips_sample = df_trips.sample(100000)

    xx, yy = pp(df_trips_sample["start_lon"].values, df_trips_sample["start_lat"].values)
    df_trips_sample["X"] = xx
    df_trips_sample["Y"] = yy

    xx, yy = pp(df_stations["start station longitude"].values, df_stations["start station latitude"].values,)
    df_stations["X"] = xx
    df_stations["Y"] = yy

    plt.close("all")
    plt.figure(figsize=(16, 9))
    plt.plot(
        df_stations["X"], df_stations["Y"], color="black", marker="+", markersize=5, linestyle="None",
    )
    plt.scatter(
        df_trips_sample["X"], df_trips_sample["Y"], c=df_trips_sample["start station id"], s=1, cmap="rainbow", alpha=0.1,
    )
    plt.axis("equal")
    plt.show()
