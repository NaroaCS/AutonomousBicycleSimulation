# AutonomousBicycleSimulation
Fleet Simulation of MIT Autonomous Bicycle Project

Main file: BikeFleetSimulation.py
To update the distribution of bikes and specially after changing the number of bikes run BikeGenerator.py


## Configuration of parameters

The parameters to be configured for this simulation can be found on the file **config.json**



**mode:** 0 for station-based, 1 for dockless, 2 for autonomous


**n_bikes:** number of bikes in the system (fleet size). **Important note:** If the number of bikes is changed, execute BikeGenerator.py to update bikes_data.xlsx


**WALK_RADIUS:** maximum walking distance for users[m]

**MAX_AUTONOMOUS_RADIUS:** maximum distance that an autonomous bike will do to pick up a user [m]


**RIDING_SPEED:** average bike riding speed of users[km/h]

**AUT_DRIVING_SPEED:** average speed of the bike in autonomous mode[km/h]

**WALKING_SPEED:** walking speed of users [km/h]


**MIN_BATTERY_LEVEL:** level at which the autonomous bikes go to a charging station [%]

**BATTERY_CONSUMPTION_METER:** battery consumption in autonomous mode [%/m]

**SF:** to assign an autonomous bike to a user the battery level has to be greater than MIN_BATTERY_LEVEL + SF*(MAX_AUTONOMOUS_RADIUS * BATTERY_CONSUMPTION_METER) where SF is a safety factor >1

**CHARGING_SPEED:** charging speed of the battery in hours for charing from 0 to 100% [h]


**BETA:** probability of a user getting a magic bike or dock, reflects the amount of rebalancing [0-1]

**MIN_N_BIKES:** minimum number of bikes that a station should have for the rebalancing action to remove a bike from that station

**MIN_N_DOCKS:** minimum number of docks that a station should have for the rebalancing action to insert a bike in that station

