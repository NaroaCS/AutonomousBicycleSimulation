---
sidebar_position: 2
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Station-based system

A station-based system consists of bicycles that can be borrowed from a docking station and must be returned to another station belonging to the same system. The docking stations are special bike racks that lock the bike and only release it by computer control. The next figure depicts the steps a user takes when using station-based BSS mode of transportation. 

<div style={{textAlign: 'center'}}>
<img src={useBaseUrl('/img/developer/user_station-1.png')} alt="user process diagram" width="50%" /> 
</div>

Users are initialized at a given location and departure time. Typically, a user checks the availability of bicycles via a smartphone application that displays the number of bikes and docks available in each station in real-time. In case there are no stations with available bikes, a bike request is made with probability $\beta$. This rebalancing action relocates a bike that is available at the nearest station, provided that the number of bikes does not fall below a predetermined minimum. If there are no stations within a walkable distance, the user might opt to use another transportation mode. In that case, the process is finalized, and the user does not complete the trip. Similarly, if there are stations but no available bicycles, the user might also decide to change the mode of transportation. 

If there are bikes within a walkable distance, the user will select the closest one to their location and will walk to that station. Sometimes, the station gets empty while the user is walking and finds no bicycles at arrival. In such cases, the user will check again for bikes in nearby stations and will repeat the process. 

Once the user has a bike, they will choose a station with available docks as close as possible to the destination. In this case, too, it might also happen that the station is full for when the user arrives, and the user will have to look for another station with available docks and bikes. Once the user has found a dock for the bike, they will lock the bicycle and walk to the final destination.

Bikes are initialized at a specified station, given that the dock capacity of that station is not exceeded. Bikes are then made available to any user. If requested, a user can unlock one bike from the station dock, becoming an unavailable bike. After being transported to another station, the bike is locked by the user and becomes available once again. This process was illustrated in the following figure:

<div style={{textAlign: 'center'}}>
<img src={useBaseUrl('/img/developer/bike_station-1.png')} alt="bike process diagram" width="20%" /> 
</div>

The configuration parameters that are specific for station-based systems are: 

| Parameter        |      Description     |   Units | 
| -------------: | :----------- | :-----: | 
| "MODE" | 0=Station-based, 1=Dockless, 2= Autonomous | [-] | 
| "NUM_BIKES" | Number of bikes in the system, fleet size | [-] | 
| "WALK_RADIUS" | Maximum distance that a user is willing to walk | [m] | 
| "RIDING_SPEED" | Average bike riding speed of users | [km/h] | 
| "WALKING_SPEED" | Walking speed of users | [km/h] | 
| "MAGIC_BETA" | Probability of a user getting an instant rebalancing; it reflects the amount of rebalancing | [0-1] | 
| "MAGIC_MIN_BIKES" | Minimum number of bikes that a station should have for the rebalancing action to remove a bike from that station | [-] | 
| "MAGIC_MIN_DOCKS" | Minimum number of docks that a station should have for the rebalancing action to insert a bike in that station | [-] |