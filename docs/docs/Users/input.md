---
sidebar_position: 1
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Input

In our case, we modeled autonomous bicycles, the used Boston-Cambridge as the scenario for our simulation, and the trip data was created based on real BlueBikes trips. You can customize any of these:

## GIS data

You will need GIS data of your chosen city/area: 
* A shapefile containing the buildings 
:::danger TODO
Add how we got it
:::
 
* a .pkl and .h5 file containing the roads

:::danger TODO
I don't have these files -> check how they're generated
:::

```shell
@staticmethod
def load(name):
    path = os.path.join("data", "graph")
    file_pkl = os.path.join(path, name + ".pkl")
    with open(file_pkl, "rb") as f:
        graph = pickle.load(f)
    file_h5 = os.path.join(path, name + ".h5")
    graph.network = pdna.Network.from_hdf5(file_h5)
    return graph
```

Buildings            |   Road network
:-------------------------:|:-------------------------:
|<div style={{textAlign: 'center'}}><img src={useBaseUrl('/img/user/boston_buildings.png')} alt="drawing" width="80%" /> </div> | <div style={{textAlign: 'center'}}> <img src={useBaseUrl('/img/user/boston_road_network.png')} alt="drawing" width="80%" /> </div>|


## User demand

The user demand data must be in a <code>.csv</code> format that has the following colums for each user: 

* "start_lat"
* "start_lon"
* "target_lat"
* "target_lon" 
* "start_time" elapsed -> # / 60  # departure time ??
* "target_time" Do we need it ? 

:::danger Review
:::

This <code>.csv</code>  must be saved under the <code>data </code> folder. The name of the .csv must be specified in <code>main.py</code>:

```
users_path = os.path.join("data", "user_trips.csv")
```

The demand considered for the simulation is based on **[Bluebikes](https://www.bluebikes.com/system-data)**  public bike-sharing system usage data. The user generation process takes advantage of this historical usage data and the buildings' spatial data. Buildings data is used to generate users' origin and destination locations inside the buildings, scattering users in buildings 300 m around stations. This process can be found <code>UserGeneration.py</code> under the folder <code>Preprocessing</code>. <code>UserGeneration.py</code> is not called every time the simulation runs because it is a time consuming process, but it can be run manually to create a new user demand file.

## Stations
:::danger Review
If users only want to simulate dockless, do they still need stations? Or should we add a random function that just leaves them at any node?
:::

The station data must be in a <code>.csv</code> format that has the following colums for each station:

* "Longitude"
* "Latitude"
* "Total docks"


The location of docking and charging stations for this simulation has also been extracted from **[Bluebikes](https://www.bluebikes.com/system-data)**. Similarly to the user demand data, the <code>.csv</code> containing the information related to the stations must be saved under the <code>data </code> folder. The name of the .csv must be specified in <code>main.py</code>:

```
stations_path = os.path.join("data", "bluebikes_stations_07_2020.csv")
```
This file is used in <code>BikeGeneration.py</code> under the folder <code>Preprocessing</code>. This code is automatically called for each simulation. In the three systems bikes are generated randomly at stations, with a probability proportional to their capacity.

:::info Review!
In the station-based system, the max number of bikes is limited to be smaller than the maximum number of docks in the system. In the dockless and the autonomous sytems, the docks are sized proportionally to the fleet size considered in that simulation.
:::




## Configuration

<code>Config.js</code> is the file where you will set the configuration of the simulations. This structure contains all the config from the three systems (SB= Station-based, DL= Dockless, AUT= Autonomous): 

| Parameter        |      Description     |   Units | Type of system |
| -------------: | :----------- | :-----: | :-----: |
| "MODE" | 0=Station-based, 1=Dockless, 2= Autonomous | [-] | SB, DL, AUT |
| "NUM_BIKES" | Number of bikes in the system, fleet size | [-] | SB, DL, AUT |
| "WALK_RADIUS" | Maximum distance that a user is willing to walk | [m] | SB, DL |
| "AUTONOMOUS_RADIUS" | Maximum distance that an autonomous bike will do to pick up a user | [m] | AUT |
| "RIDING_SPEED" | Average bike riding speed of users | [km/h] | SB, DL, AUT |
| "WALKING_SPEED" | Walking speed of users | [km/h] | SB, DL |
| "AUTONOMOUS_SPEED" | Average speed of the bike in autonomous mode | [km/h] | AUT |
| "BATTERY_MIN_LEVEL" | Level at which the autonomous bikes go to a charging station | [%] | AUT |
| "BATTERY_AUTONOMY" | Autonomy of the autonomous bikes | [km] | AUT |
| "BATTERY_CHARGE_TIME" | Time that it takes to charge a battery from 0 to 100% | [h] | AUT |
| "INSTANT_BETA" | Probability of a user getting an instant rebalancing; it reflects the amount of rebalancing | [0-1] | SB |
| "INSTANT_MIN_BIKES" | Minimum number of bikes that a station should have for the rebalancing action to remove a bike from that station | [-] | SB |
| "INSTANT_MIN_DOCKS" | Minimum number of docks that a station should have for the rebalancing action to insert a bike in that station | [-] | SB |





