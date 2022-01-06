#Author: Naroa CS
#Date: Wed Jan 6 13:52:20

import pandas as pd
import numpy as np


df_1 = pd.read_csv("./results/2022-01-06_12-04-31/bike_trips.csv")
df_2 = pd.read_csv("./results/2022-01-06_12-21-30/bike_trips.csv")
df_3 = pd.read_csv("./results/2022-01-06_12-59-15/bike_trips.csv")
df_4 = pd.read_csv("./results/2022-01-06_13-35-34/bike_trips.csv")
df_5 = pd.read_csv("./results/2022-01-06_13-58-44/bike_trips.csv")

#TOTAL DISTANCE

total_dist_1= df_1['time_ride'].sum()*8/3.6 # units [m] // speed is 8 km/h time_ride is in s
total_dist_2= df_2['time_ride'].sum()*8/3.6 
total_dist_3= df_3['time_ride'].sum()*8/3.6 
total_dist_4= df_4['time_ride'].sum()*8/3.6 
total_dist_5= df_5['time_ride'].sum()*8/3.6 


#CHARGE DISTANCE

df_1_charge=df_1.loc[df_1['trip_type']==2]
charge_dist_1=df_1_charge['time_ride'].sum()*8/3.6

df_2_charge=df_2.loc[df_2['trip_type']==2]
charge_dist_2=df_2_charge['time_ride'].sum()*8/3.6

df_3_charge=df_3.loc[df_3['trip_type']==2]
charge_dist_3=df_3_charge['time_ride'].sum()*8/3.6

df_4_charge=df_4.loc[df_4['trip_type']==2]
charge_dist_4=df_4_charge['time_ride'].sum()*8/3.6

df_5_charge=df_5.loc[df_5['trip_type']==2]
charge_dist_5=df_5_charge['time_ride'].sum()*8/3.6

pct_1_charge=charge_dist_1/total_dist_1*100
pct_2_charge=charge_dist_2/total_dist_2*100
pct_3_charge=charge_dist_3/total_dist_3*100
pct_4_charge=charge_dist_4/total_dist_4*100
pct_5_charge=charge_dist_5/total_dist_5*100


#USER DISTANCE

df_1_use=df_1.loc[df_1['trip_type']==0]
use_dist_1=df_1_use['time_ride'].sum()*8/3.6

df_2_use=df_2.loc[df_2['trip_type']==0]
use_dist_2=df_2_use['time_ride'].sum()*8/3.6

df_3_use=df_3.loc[df_3['trip_type']==0]
use_dist_3=df_3_use['time_ride'].sum()*8/3.6

df_4_use=df_4.loc[df_4['trip_type']==0]
use_dist_4=df_4_use['time_ride'].sum()*8/3.6

df_5_use=df_5.loc[df_5['trip_type']==0]
use_dist_5=df_5_use['time_ride'].sum()*8/3.6

pct_1_use=use_dist_1/total_dist_1*100
pct_2_use=use_dist_2/total_dist_2*100
pct_3_use=use_dist_3/total_dist_3*100
pct_4_use=use_dist_4/total_dist_4*100
pct_5_use=use_dist_5/total_dist_5*100

#PICKUP DISTANCE

df_1_pickup=df_1.loc[df_1['trip_type']==1]
pickup_dist_1=df_1_pickup['time_ride'].sum()*8/3.6

df_2_pickup=df_2.loc[df_2['trip_type']==1]
pickup_dist_2=df_2_pickup['time_ride'].sum()*8/3.6

df_3_pickup=df_3.loc[df_3['trip_type']==1]
pickup_dist_3=df_3_pickup['time_ride'].sum()*8/3.6

df_4_pickup=df_4.loc[df_4['trip_type']==1]
pickup_dist_4=df_4_pickup['time_ride'].sum()*8/3.6

df_5_pickup=df_5.loc[df_5['trip_type']==1]
pickup_dist_5=df_5_pickup['time_ride'].sum()*8/3.6

pct_1_pickup=pickup_dist_1/total_dist_1*100
pct_2_pickup=pickup_dist_2/total_dist_2*100
pct_3_pickup=pickup_dist_3/total_dist_3*100
pct_4_pickup=pickup_dist_4/total_dist_4*100
pct_5_pickup=pickup_dist_5/total_dist_5*100


#PRINTS

total_m= (total_dist_1+total_dist_2+total_dist_3+total_dist_4+total_dist_5)/5
print('TOTAL DIST [km]: ', total_m/1000)

avg_pct_use=(pct_1_use+pct_2_use+pct_3_use+pct_4_use+pct_5_use)/5
print('USE [%]: ', avg_pct_use)

avg_pct_pickup=(pct_1_pickup+pct_2_pickup+pct_3_pickup+pct_4_pickup+pct_5_pickup)/5
print('PICK UP [%]: ', avg_pct_pickup)

avg_pct_charge=(pct_1_charge+pct_2_charge+pct_3_charge+pct_4_charge+pct_5_charge)/5
print('CHARGE [%]: ', avg_pct_charge)