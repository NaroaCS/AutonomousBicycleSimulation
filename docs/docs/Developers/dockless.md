---
sidebar_position: 3
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Dockless system

In dockless system, the users check for available bicycles in an app that shows the location of available bicycles. If there are no bicycles within a walkable distance, the users might choose to use another transportation mode. If there are bicycles within a walkable radius, the user will walk to the closest one. If the bike is no longer available at arrival because someone else took it already, the user will look for another bike and repeat the process. Finally, the user will ride the bike and drop it off right at the destination. The next figure illustrates the steps a user takes when using station-based BSS mode of transportation. 

<div style={{textAlign: 'center'}}>
<img src={useBaseUrl('/img/developer/user_dockless-1.png')} alt="user process diagram" width="30%" /> 
</div>
The bike process is almost identical to the station-based bike process. In the case of the dockless system, no rebalancing was considered. Most of the rebalancing in these systems occurs from the outskirts to the city center and, in the case of this simulation, the trips are restricted to be on the area around where the bike-sharing system operates. 

<div style={{textAlign: 'center'}}>
<img src={useBaseUrl('/img/developer/bike_dockless-1.png')} alt="bike process diagram" width="20%" /> 
</div>

The configuration parameters for dockless systems are:

| Parameter        |      Description     |   Units | 
| -------------: | :----------- | :-----: |
| "MODE" | 0=Station-based, 1=Dockless, 2= Autonomous | [-] | 
| "NUM_BIKES" | Number of bikes in the system, fleet size | [-] | 
| "WALK_RADIUS" | Maximum distance that a user is willing to walk | [m] | 
| "RIDING_SPEED" | Average bike riding speed of users | [km/h] | 
| "WALKING_SPEED" | Walking speed of users | [km/h] | 


