---
sidebar_position: 3
label: Results
---

# Reading the results 

The results are stored in the <code>results</code> folder. The subfolder with the results of an specific simulation will have the date and time of the moment when it was launched as a name in <code>%Y-%m-%d_%H-%M-%S</code> format.

For each simulation there are four files that are saved: <code>user_trips.csv</code>, <code>bike_trips.csv</code>, <code>config.json</code> and <code>app.log</code>.

## User trips 

The structure of the <code>user_trips.csv</code> file can be found in the <code>UserTrip.py</code> under the folder <code>src</code>. The format is the same for the three types of system SB= Station-based, DL= Dockless, AUT= Autonomous. This output file contains the following colums:

| Parameter        |      Description     |  Type of system |
| -------------: | :----------- |:-----: |
| user_id | The id of the user who made the trip | SB, DL, AUT |
| status | The user finished the tip (finished), there were no bikes in a walkable distance (no_bikes), there was no walkable station at the beginning of the trip (not_walkable_stations), there was no end station walkable or not walkable(no_end_station)| SB |
| bike_id | The id of the bike used for that trip | SB, DL, AUT |
| mode | 0=Station-based, 1=Dockless, 2= Autonomous |  SB, DL, AUT |
| time_departure | Elapsed time at the beginning of the trip [s] | SB, DL, AUT |
| time_target | Elapsed time at arrival [s] | SB, DL, AUT |
| time_walk_origin | Duration of the walk from the departure point to the bike/station [s] | SB, DL |
| time_ride | Duration of the bike ride [s] | SB, DL, AUT |
| time_wait| Duration of the wait time at the beginning of the trip [s] | AUT |
| time_walk_destination | Duration of the walk at the end of the trip from the station to the destination [s] | SB |
| origin_lon| Longitude of the departure point | SB, DL, AUT |
| origin_lat| Latitude of the departure point | SB, DL, AUT |
| destination_lon | Longitude of the destination point | SB, DL, AUT |
| destination_lat| Latitude of the destination point | SB, DL, AUT |
| origin_visited_stations| List of the ids of the stations visited until finding an available bike | SB |
| destination_visited_stations| List of the ids of the stations visited until finding an available dock | SB |
| origin_station| The id of the station where the user got the bike | SB |
| destination_station| The id of the station where the user left the bike | SB |
| instant_bike| Indicates if the used bike was an instantaneously rebalanced bike (1) or not (0) | SB, AUT |
| instant_dock| Indicates if the used dock was liberated by an instantaneously rebalanced bike (1) or not (0)  | SB|
| bike_lon| Longitude of the location of the bike chosen for the trip | DL, AUT |
| bike_lat| Latitude of the location of the bike chosen for the trip| DL, AUT |



## Bike trips 

The structure of the <code>bike_trips.csv</code> file can be found in the <code>BikeTrip.py</code> under the folder <code>src</code>. The format is the same for the three types of system SB= Station-based, DL= Dockless, AUT= Autonomous. This output file contains the following columns:

| Parameter        |      Description     |  Type of system |
| -------------: | :----------- |:-----: |
| bike_id | The id of the bike that made the trip | SB, DL, AUT |
| user_id | The id of the user who made the trip | SB, DL, AUT |
| mode | 0=Station-based, 1=Dockless, 2= Autonomous |  SB, DL, AUT |
| trip_type | 1=User drive, 2=Charge trip, 3=Rebalancing trip|  AUT |
| time_departure | Elapsed time at the beginning of the trip [s] | SB, DL, AUT |
| time_ride | Duration of the bike ride [s] | SB, DL, AUT |
| time_charge | Duration of the bike charging process [s] | AUT |
| instant_bike| Indicates if the used bike was an instantaneously rebalanced bike (1) or not (0) | SB, AUT |
| instant_dock| Indicates if the used dock was liberated by an instantaneously rebalanced bike (1) or not (0)  | SB|
| origin_station| The id of the station where the user got the bike | SB |
| destination_station| The id of the station where the user left the bike | SB |
| origin_lon| Longitude of the departure point | SB, DL, AUT |
| origin_lat| Latitude of the departure point | SB, DL, AUT |
| destination_lon | Longitude of the destination point | SB, DL, AUT |
| destination_lat| Latitude of the destination point | SB, DL, AUT |
| battery_in| Battery at the beginning of the trip/process | AUT |
| battery_out| Battery at the end of the trip/process  | AUT |

:::note Review
The charging trips have just one line? or do we also save the battery at arrival to the station?
Yes, we only do save the battery at the end of the trip. We could include another column to save these three values: at the beginning of the process, at the charging station arrival, and at the end of the process (which in this case should be full battery 100%).
::: 

## Configuration

The <code>config.json</code> file saves the parameters that were used when running this simulation

## Logging

The <code>app.log</code> file saves the log of the actions. 

:::note Review
Do we have the app.log active? How do we activate/deactivate?
The logging can be activated and deactivated on the Results.py file, commenting out the *self.setup_log()* command.
We could take this parameter up to the SimulationEngine to be easier to change.
::: 
