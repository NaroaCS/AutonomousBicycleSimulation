#MAIN
# This is the beggining of the code

#LIBRARIES
import simpy #For sequential coding
import random 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#INPUT OF DATA
data={}
#map

# station information

#bike information for SB -> id and initial station id

#bike information for dockless and autonomous -> id and location(lat,lon)

#OD matrix
df=pd.read_excel('output.xlsx')


#Initialize bikes

#PARAMETERS/CONFIGURATION
mode=2 # 0 for StationBased / 1 for Dockless / 2 for Autonomous

#DEFINITION OF CLASSES
class City:
    def __init__(self, env, data): #Constructor is automatically called when you create a new instance of a class
            self.env = env #Takes simulation environment
            self.data = data #Its the city that takes the initial data and sets it 

            self.stations = [] #defines arrays of objects of different classes within itself
            self.bikes = []
            self.agents = []

            self.start()
    def start(self): #Start calls to the initialization of station, bikes, agents
            self.init_stations()
            self.init_bikes()
            self.init_agents()

    def init_stations(self):
            #Takes data of stations and goes one by one adjudicating the data to the station objects (that now have an id)
            for station_id, station_data in enumerate(self.data['stations']): 
                station = Station(self.env, station_id)  
                station.set_capacity(station_data['capacity']) 
                station.set_location(np.array(station_data['location'])) 
                station.init_station() #initialize that station (resource and container)
                self.stations.append(station) #Adds station to the staions array in city

    def init_bikes(self):
            for bike_id, bike_data in enumerate(self.data['bikes']): 
                #mode = bike_data['mode'] #Takes the mode 
                if mode == 0:
                    bike = StationBike(self.env, bike_id) 
                    station_id = bike_data['station'] #The initial station is provided in the data
                    self.stations[station_id].push_bike(bike_id) #Saves bike in station
                    bike.set_station(station_id)  # saves station in bike
                    bike.set_location(self.stations[station_id].location)  #Saves the location of the station as its location
                elif mode == 1:
                    bike = DocklessBike(self.env, bike_id) #creates object of class Dockless Bike with the env and the id as imput
                    bike.set_location(np.array(bike_data['location'])) #initial location is given, so it takes it and saves it
                elif mode == 2:
                    bike = AutonomousBike(self.env, bike_id) #creates object of class Autonomous Bike with the env and the id as imput
                    bike.set_location(np.array(bike_data['location'])) #initial location is given, so it takes it and saves it
                self.bikes.append(bike) #Adds bike to the array of Bikes in city

    def init_agents(self):
            for agent_id, agent_data in enumerate(self.data['agents']): #saves agents data
                #Creates a different class of agent depending on the mode
                origin=agent_data['origin']
                destination=agent_data['destination']
                time=agent_data['timestamp']
                if mode == 0:
                    agent = AgentSB(self.env, agent_id, origin, destination, time)
                elif mode == 1:
                    agent = AgentDL(self.env, agent_id, origin, destination, time)
                elif mode == 2:
                    agent = AgentAut(self.env, agent_id, origin, destination, time)
                agent.start()  
                self.agents.append(agent) #Adds the agent to the array of agents in city

class Bike:
    def __init__(self,env, bike_id):
        self.env=env
        self.bike_id=bike_id
        self.location=None
        #self.agent=None
    # def UpdateLocation(self,location):
    #      self.location = location

    def update_agent(self,agent_id):
        self.agent = agent_id

    def delete_agent(self):
        self.agent = None

    def vacant(self):
        if (self.agent is None):
            return True

    def ride(self,destination):
        #Here it should call the routing algotithm
        # time=routing(self.location,destination,bikingspeed)
        distance = self.dist(self.location, destination)
        yield self.env.timeout(distance)
        self.location = destination
        #save this info in SystemStateData
        
class StationBike(Bike):
    def __init__(self,env):
        self.env=env
class DocklessBike(Bike):
    def __init__(self,env):
        self.env=env
class AutonomousBike(Bike):
    def __init__(self,env):
        self.env=env
        self.reservation_id= None
    def reserved(self):
        if (self.reservation_id is not None):
            return True

    def go_towards(self, target_location):
        #This is for the demand prediction
        distance = self.dist(self.location, target_location) #This should be routing
        yield self.env.timeout(distance)
        self.location = target_location

    def autonomous_drive(self, user_location):
        #Autonomous drive to pick up the user
        distance = self.dist(self.location, user_location) #This should be routing
        yield self.env.timeout(distance)
        self.location =user_location
        #Save pickup and update


class Station:
    def __init__(self,env,station_id):
        self.env=env
        self.station_id=station_id
        self.location = None
        self.capacity = None

    def init_station(self): #parameters that help to manage the station
        self.resource = simpy.Resource(self.env, capacity=1) # Put some order in case 2 arrite at the same time Do we need this ? If all slots are taken, requests are enqueued. Once a usage request is released, a pending request will be triggered
        self.container = simpy.Container(self.env, self.capacity, init=0) #It supports requests to put or get matter into/from the container
   
    def has_bikes(self):
        return self.container.level > 0

    def has_docks(self):
        return self.capacity - self.container.level > 0

    def empty(self):
        return self.container.level == 0

    def full(self):
        return self.container.level == self.capacity

    def push_bike(self, bike_id):
        if self.has_docks(): #check that there are docks available
            self.container.put(1) #add one item 
            self.bikes.append(bike_id) #add the bike's id
            #Save in SystemStateData
        else:
            print('[%.2f] Station %d has no docks available' %
              (self.env.now, self.station_id))

    def pull_bike(self):
        if self.has_bikes(): #Check that it has bikes
            self.container.get(1) #Counts that there is one less
            bike_id=random.choice(self.bikes) #chooses a random bike
            self.bikes.remove(bike_id) #removes that bike from the list
            #Save in SystemStateData
        else:
            print('[%.2f] Station %d has no bikes available' %
              (self.env.now, self.station_id))
        


class Agent:
    def __init__(self,env,agent_id, origin, destination, time):
        self.env=env
        self.agent_id=agent_id
        self.location= None
        self.state=None #None, walking,waiting,biking
        self.event_setup_task = self.env.event() # ?¿ Here or in a start() function
        self.bike_id=None

        self.origin=None
        self.destination=None
        self.time=None
    
    def process(self):

        # 1-Init on source
        yield self.env.process(self.init_agent())


    def init_agent(self):
        yield self.env.timeout(self.time) #waits until its the hour
        self.location = self.origin
        if self.print:
            print('[%.2f] Agent %d initialized at location [%.2f, %.2f]' %
                  (self.env.now, self.agent_id, *self.location))

    def walk_to(self, location):
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)
        self.location = location

    def ride_bike_to(self, location):

        bike = self.bikes[self.bike_id]
        yield self.env.process(bike.ride(location))
        self.location = location
    
class AgentSB(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)  #????

class AgentDL(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)  #????

class AgentAut(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)  #????

class SystemStateData:
    #location of bikes, situaition of stations
    #it is updated by user trips and the FleetManager
    def __init__(self,env):
        self.env=env
class RebalancingManager:
    #makes rebalancing decisions for SB and dockless
    def __init__(self,env):
        self.env=env
class DemandPredictionManager:
    #predictive rebalancing for autonomous
    def __init__(self,env):
        self.env=env
class ChargeManager:
    #makes recharging decisions
    def __init__(self,env):
        self.env=env
class DemandManager:
    #receives orders from users and decides which bike goes
    def __init__(self,env):
        self.env=env
class FleetManager:
    #sends the decisions to the bikes
    #updates SystemStateData
    def __init__(self,env):
        self.env=env

#MAIN BODY - SIMULATION AND HISTORY GENERATION
env = simpy.Environment()
city = City(env, map)
env.run(until=1000)