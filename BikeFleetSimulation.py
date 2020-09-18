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
WALK_RADIUS = 50

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
            datainterface=DataInterface(env)
            for agent_id, agent_data in enumerate(self.data['agents']): #saves agents data
                #Creates a different class of agent depending on the mode
                origin=agent_data['origin']
                destination=agent_data['destination']
                time=agent_data['timestamp']
                if mode == 0:
                    agent = StationBasedAgent(self.env, agent_id, origin, destination, time)
                elif mode == 1:
                    agent = DocklessAgent(self.env, agent_id, origin, destination, time)
                elif mode == 2:
                    agent = AutonomousAgent(self.env, agent_id, origin, destination, time)
                agent.start() 
                agent.set_data(self.data['grid'], self.stations, self.bikes)  
                self.agents.append(agent) #Adds the agent to the array of agents in city

class Bike:
    def __init__(self,env, bike_id):
        self.env=env
        self.bike_id=bike_id
        self.location=None
        self.agent=None
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

    def dist(self, a, b): #delete after instering routing
        return np.linalg.norm(a - b)
       
class StationBike(Bike):
    def __init__(self,env):
        self.env=env
        self.station_id = None

    def set_station(self, station_id):
        self.station_id = station_id

    def pop_station(self):
        self.station_id = None

    def register_pull(self, agent_id):
        self.set_agent(agent_id)
        self.pop_station()

    def register_push(self, station_id):
        self.delete_agent()
        self.set_station(station_id)
    
    def docked(self):
        return self.station_id is not None

class DocklessBike(Bike):
    def __init__(self, env, bike_id):
        super().__init__(env, bike_id)        
        self.init_state()

    def unlock(self, agent_id):
        self.set_agent(agent_id)

    def lock(self):
        self.delete_agent()

class AutonomousBike(Bike):
    def __init__(self,env):
        self.env=env
        self.reserved=False
    
    def call(self, agent_id):
         self.set_agent(agent_id)
         reserved= True

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
    def drop(self):
        self.delete_agent()
        self.reserved= False
        
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
        # self.stations = None
        # self.bikes = None

        self.agent_id=agent_id
        self.location= None
        self.state=None #None, walking,waiting,biking
        self.event_setup_task = self.env.event() # ?¿ Here or in a start() function
        self.bike_id=None

        self.origin=None
        self.destination=None
        self.time=None
    
    def set_data(self, grid, stations, bikes):
        self.grid = grid
        self.stations = stations
        self.bikes = bikes

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
        #Here it should call routing
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)
        self.location = location

    def ride_bike_to(self, location):
        bike = self.bikes[self.bike_id]
        yield self.env.process(bike.ride(location)) #ride is a function in bike, not agent
        self.location = location
    
    def dist(self, a, b):
        return np.linalg.norm(a - b)

class StationBasedAgent(Agent):
    def __init__(self, env, datainterface, agent_id,location):
        super().__init__(env, agent_id)
        self.datainterface=datainterface

    def start(self):
        super().start()

        # STATION-BASED
        self.station_id = None
        self.event_select_station = self.env.event()
        self.event_interact_bike = self.env.event()
        self.visited_stations = []
        #self.station_history = []

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on source
        yield self.env.process(super().process())

        self.event_interact_bike = self.env.event() #this structure is a bit confusing
        while not self.event_interact_bike.triggered:
            # 2-Select source station
            [station, station_location, visited_stations]=self.select_start_station(self.location,self.visited_stations)
            yield self.event_select_station
            #station = self.stations[self.station_id]

            # 3-Walk to source station
            yield self.env.process(self.walk_to(station_location))

            # 4-Pull bike
            yield self.env.process(self.interact_bike(action='pull'))
            
        self.event_interact_bike = self.env.event()
        visited_stations.clear() #here we should zero it because one might do a round trip
        
        while not self.event_interact_bike.triggered:
            # 5-Select target station
            [station, station_location, visited_stations]=self.select_end_station(self.location,self.visited_stations)
            yield self.event_select_station
            #station = self.stations[self.station_id]

            # 6-Ride bike
            yield self.env.process(self.ride_bike_to(station_location))

            # 7-Push bike
            yield self.env.process(self.interact_bike(action='push'))

        # 8-Walk to target
        yield self.env.process(self.walk_to(self.target))
    
        # 9-Save state
        # self.save_state()

        # # 10-Finish
        yield self.env.timeout(10)
        # if self.print:
        #     print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))
    
    def select_start_station(self,location,visited_stations):
        selected_station_info=self.datainterface.select_start_station(location,visited_stations)
        return selected_station_info

    def select_end_station(self,location,visited_stations):
        selected_station_info=self.datainterface.select_end_station(location,visited_stations)
        return selected_station_info

    #def update_station_info(self, location): 
        # values = []
        # for station in self.stations:
        #     station_id = station.station_id
        #     has_bikes = station.has_bikes()
        #     has_docks = station.has_docks()
        #     visited = station_id in self.visited_stations
        #     distance = self.dist(location, station.location) 
        #     walkable = distance < WALK_RADIUS
        #     values.append((station_id, has_bikes, has_docks,
        #                    visited, distance, walkable))
        # labels = ['station_id', 'has_bikes', 'has_docks',
        #           'visited', 'distance', 'walkable']
        # types = [int, int, int,
        #          int, float, int]
        # dtype = list(zip(labels, types))
        # self.station_info = np.array(values, dtype=dtype)

    #def select_station(self, aim):
        # self.event_select_station = self.env.event()
        # if aim=='source':
        #     location=self.location
        # else:
        #     location=self.target

        # self.update_station_info(location)

        # for e in np.sort(self.station_info, order='distance'):
        #     if aim == 'source':
        #         valid = e['has_bikes'] and not e['visited'] and e['walkable']
        #     else:
        #         valid = e['has_docks'] and not e['visited'] and e['walkable']
        #     if valid:
        #         self.station_id = e['station_id']
        #         self.visited_stations.append(self.station_id)
        #         self.event_select_station.succeed()
                
        # if not self.event_select_station.triggered:
        #     print("No bikes/docks found in a walkable distance")

    def interact_bike(self, action):
        station = self.stations[self.station_id]

        #Check if there are still bikes/docks at arrival
        if action=='pull':
            valid=station.has_bikes()
        else:
            valid=station.has_docks()
    
        if valid:
            if action == 'pull':
                self.bike_id = station.choose_bike()
                self.bikes[self.bike_id].register_pull(self.agent_id) #saves the pull in bike
                station.pull_bike(self.bike_id) #saves the pull in station
            else:
                self.bikes[self.bike_id].register_push(self.station_id)
                station.push_bike(self.bike_id)

            self.event_interact_bike.succeed()

            yield self.env.timeout(1)
        else:
            # self.time_interact_bike = None
            # if self.print:
            #     print('[%.2f] Station %d has zero %s available' %
            #            (self.env.now, self.station_id, 'bikes' if action == 'pull' else 'docks'))
            # yield self.env.timeout(3)
            print("There were no bikes/docks at arrival!")
              
class DocklessAgent(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)
        self.datainterface=datainterface
    def start(self):
        super().start()

        # DOCKLESS
        self.dockless_bike_id = None
        #self.dockless_history = []

        self.event_select_dockless_bike = self.env.event()
        self.event_unlock_bike = self.env.event()

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on source
        yield self.env.process(super().process())

        while not self.event_unlock_bike.triggered:
            # 2-Select dockless bike
            [dockless_bike,dockless_bike_location]=self.select_dockless_bike(self.location)
            yield self.event_select_dockless_bike
            #dockless_bike = self.bikes[self.dockless_bike_id]

            # 3-Walk to dockless bike
            yield self.env.process(self.walk_to(dockless_bike_location))

            # 4-Unlock bike
            yield self.env.process(self.unlock_bike())

        # 5-Ride bike
        yield self.env.process(self.ride_bike_to(self.target))

        # 6-Drop bike
        self.lock_bike()

        # 7-Save state
        #self.save_state()

        # # 8-Finish
        yield self.env.timeout(10)
        # if self.print:
        #     print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))


    #def update_bike_info(self): 
        # values = []
        # for bike in self.bikes:
        #     if isinstance(bike, DocklessBike):
        #         bike_id = bike.bike_id
        #         rented = bike.rented()
        #         distance = self.dist(self.location, bike.location)
        #         walkable = distance < WALK_RADIUS
        #         values.append((bike_id, rented, distance, walkable))
        # labels = ['bike_id', 'rented', 'distance', 'walkable']
        # types = [int, int, float, int]
        # dtype = list(zip(labels, types))
        # self.bike_info = np.array(values, dtype=dtype)

    #def select_dockless_bike(self):
        # self.event_select_dockless_bike = self.env.event()
        # self.update_bike_info()
        # for e in np.sort(self.bike_info, order='distance'):
        #     valid = not e['rented'] and e['walkable']
        #     if valid:
        #         self.dockless_bike_id = e['bike_id']
        #         self.event_select_dockless_bike.succeed()

        # if not self.event_select_dockless_bike.triggered:
        #     print("No bikes in walkable distance")
           
    def select_dockless_bike(self,location):
        selected_bike_info=self.datainterface.select_dockless_bike(location)
        return selected_bike_info

    def unlock_bike(self):
        dockless_bike = self.bikes[self.dockless_bike_id]
        if not dockless_bike.rented():
            yield self.env.timeout(1)
            self.bike_id = dockless_bike.bike_id
            dockless_bike.unlock(self.agent_id)
            #HERE IT DOESNT SAVE THAT IT HAS BEEN RENTED
            self.event_unlock_bike.succeed()
        else:
            yield self.env.timeout(3)
            print('Bike has already been rented')

    def lock_bike(self):
        bike = self.bikes[self.bike_id]
        bike.lock()

class AutonomousAgent(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)

    def start(self):
        super().start()

        # AUTONOMOUS
        self.event_call_autonomous_bike = self.env.event()
       # self.autonomous_history = []

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on source
        yield self.env.process(super().process())

        # 2-Call autonomous bike
        self.call_autonomous_bike()
        yield self.event_call_autonomous_bike

        # 3-Wait for autonomous bike
        autonomous_bike = self.bikes[self.bike_id]
        yield self.env.process(autonomous_bike.autonomous_move(self.location))

        # 4-Ride bike
        yield self.env.process(self.ride_bike_to(self.target))

        # 5-Drop bike
        self.drop_bike()

        # 6-Save state
        #self.save_state()

        # 7-Finish
        yield self.env.timeout(10)
        # if self.print:
        #     print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))


    def update_bike_info(self):  ##Isinstannce???
        values = []
        for bike in self.bikes:
            if isinstance(bike, AutonomousBike):
                bike_id = bike.bike_id
                rented = bike.rented()
                distance = self.dist(self.location, bike.location)
                walkable = distance < WALK_RADIUS
                values.append((bike_id, rented, distance, walkable))
        labels = ['bike_id', 'rented', 'distance', 'walkable']
        types = [int, int, float, int]
        dtype = list(zip(labels, types))
        self.bike_info = np.array(values, dtype=dtype)

    def call_autonomous_bike(self):  #This should be transferred to the demand manager / Here it is not 'walkabke'
        self.event_call_autonomous_bike = self.env.event()
        self.update_bike_info()
        for e in np.sort(self.bike_info, order='distance'):
            valid = not e['rented'] and e['walkable']
            if valid:
                self.bike_id = e['bike_id']
                self.bikes[self.bike_id].call(self.agent_id)
                self.event_call_autonomous_bike.succeed()

        if not self.event_call_autonomous_bike.triggered:
            print("No autonomous bikes in XX miles")
    

    def drop_bike(self):
        bike = self.bikes[self.bike_id]
        bike.drop()

class SystemData: #Put inside of City
    #location of bikes, situaition of stations
    #it is updated by user trips and the FleetManager
    def __init__(self,env):
        self.env=env
class DataInterface:
    #retreives info from SystemData
    def __init__(self,env):
        self.env=env

    def set_data(self, grid, stations, bikes):
        self.grid = grid
        self.stations = stations
        self.bikes = bikes

    def dist(self, a, b):
        return np.linalg.norm(a - b)

    def select_start_station(self,location,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_bikes = station.has_bikes()
            visited = station_id in visited_stations
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.latitude
            lon=station.longitude
            values.append((station_id, has_bikes,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_bikes',
                  'visited', 'distance', 'walkable', 'lat','lon']
        types = [int, int,
                 int, float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        self.event_select_station = self.env.event()

        for e in np.sort(station_info, order='distance'):
            valid = e['has_bikes'] and not e['visited'] and e['walkable']
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)   
                self.event_select_station.succeed()        
                
        if not self.event_select_station.triggered:
            print("No bikes found in a walkable distance")
        station_location=[lat,lon]
        return [station_id, station_location, visited_stations] 

    def select_end_station(self,location,visited_stations):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_docks = station.has_docks()
            visited = station_id in visited_stations
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            lat=station.latitude
            lon=station.longitude
            values.append((station_id, has_docks,
                           visited, distance, walkable, lat, lon))
        labels = ['station_id', 'has_docks',
                  'visited', 'distance', 'walkable', 'lat','lon']
        types = [int, int, 
                 int, float, int, float, float]
        dtype = list(zip(labels, types))
        station_info = np.array(values, dtype=dtype)

        self.event_select_station = self.env.event()

        for e in np.sort(station_info, order='distance'):
            valid = e['has_docks'] and not e['visited'] and e['walkable']
            if valid:
                station_id = e['station_id']
                lat=e['lat']
                lon=e['lon']
                visited_stations.append(station_id)
                self.event_select_station.succeed()        
                
        if not self.event_select_station.triggered:
            print("No docks found in a walkable distance")
        station_location=[lat,lon]
        return [station_id,station_location,visited_stations]

    def select_dockless_bike(self,location):

        values = []

        for bike in self.bikes:
            if isinstance(bike, DocklessBike):
                bike_id = bike.bike_id
                rented = bike.rented()
                distance = self.dist(location, bike.location)
                walkable = distance < WALK_RADIUS
                lat=bike.latitude
                lon=bike.longitude
                values.append((bike_id, rented, distance, walkable,lat,lon))
        labels = ['bike_id', 'rented', 'distance', 'walkable','lat','lon']
        types = [int, int, float, int,float,float]
        dtype = list(zip(labels, types))
        bike_info = np.array(values, dtype=dtype)

        self.event_select_dockless_bike = self.env.event()

        for e in np.sort(bike_info, order='distance'):
            valid = not e['rented'] and e['walkable']
            if valid:
                dockless_bike_id = e['bike_id']
                lat=e['lat']
                lon=e['lon']
                self.event_select_dockless_bike.succeed()

        if not self.event_select_dockless_bike.triggered:
            print("No bikes in walkable distance")
        bike_location=[lat,lon]
        return [dockless_bike_id,bike_location]


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
datainterface=DataInterface(env,)
env.run(until=1000)