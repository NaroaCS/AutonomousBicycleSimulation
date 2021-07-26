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

Eg. Buildings
<img src={useBaseUrl('/img/user/boston_buildings.png')} alt="drawing" width="40%" /> 

Eg. Road network
<img src={useBaseUrl('/img/user/boston_road_network.png')} alt="drawing" width="40%" /> 


## OD matrix

:::danger TODO
:::

## Stations -> alternatives (?)
:::danger TODO
:::

## Config.js

This is the file where you will set the configuration of the simulations. This structure contains all the config from the three systems (SB= Station-based, DL= Dockless, AUT= Autonomous): 

| Parameter        |      Description     |   Units | Type of system |
| -------------: | :----------- | :-----: | :-----: |
| "MODE" | 0=Station-based, 1=Dockless, 2= Autonomous | [-] | (SB, DL, AUT) |
| "NUM_BIKES" | Number of bikes in the system, fleet size | [-] | (SB, DL, AUT) |
| "WALK_RADIUS" | Maximum distance that a user is willing to walk | [m] | (SB, DL) |
| "AUTONOMOUS_RADIUS" | Maximum distance that an autonomous bike will do to pick up a user | [m] | (AUT) |
| "RIDING_SPEED" | Average bike riding speed of users | [km/h] | (SB, DL, AUT) |
| "WALKING_SPEED" | Walking speed of users | [km/h] | (SB, DL) |
| "AUTONOMOUS_SPEED" | Average speed of the bike in autonomous mode | [km/h] | (AUT) |
| "BATTERY_MIN_LEVEL" | Level at which the autonomous bikes go to a charging station | [%] | (AUT) |
| "BATTERY_AUTONOMY" | Autonomy of the autonomous bikes | [km] | (AUT) |
| "BATTERY_CHARGE_TIME" | Time that it takes to charge a battery from 0 to 100% | [h] | (AUT) |
| "MAGIC_BETA" | Probability of a user getting an instant rebalancing; it reflects the amount of rebalancing | [0-1] | (SB) |
| "MAGIC_MIN_BIKES" | Minimum number of bikes that a station should have for the rebalancing action to remove a bike from that station | [-] | (SB) |
| "MAGIC_MIN_DOCKS" | Minimum number of docks that a station should have for the rebalancing action to insert a bike in that station | [-] |(SB) |





