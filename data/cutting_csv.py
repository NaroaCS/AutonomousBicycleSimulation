#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 11:16:02 2021

@author: NaroaCS
"""
# %%
import numpy as np
import pandas as pd
import random

# %% IMPORT TRIPS

df_trips = pd.read_csv("./data/user_trips.csv")

# DATE FILTER
start_date = "2019-10-07 00:00:00"
end_date = "2019-10-14 00:00:00"
df_trips = df_trips[df_trips["starttime"].between(start_date, end_date)]

#SAVE DATA
df_trips.to_csv("./data/user_trips_0.csv", index=False)