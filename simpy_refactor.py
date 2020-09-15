
# %%
import simpy
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

WALK_RADIUS = 50
# TO-DO:
# parametrize speeds
# include gis maps


#####    INPUT OF DATA #####
data = {
    #Size of the grid
    'grid': {
        'xlim': [0, 100],
        'ylim': [0, 100]
    },
    #Docking stations with their location and capacity
    'stations': [
        {
            'location': [5, 5],
            'capacity': 3
        },
        {
            'location': [10, 10],
            'capacity': 3
        },
        {
            'location': [90, 90],
            'capacity': 2
        },
        {
            'location': [95, 95],
            'capacity': 2
        }
    ],
    # All the bikes (0=SB; 1=Dockless,2=Autonomous) and their initial locations
    'bikes': [
        {'mode': 0, 'station': 0},
        {'mode': 0, 'station': 0},
        {'mode': 0, 'station': 1},
        {'mode': 0, 'station': 2},
        {'mode': 0, 'station': 3},
        {'mode': 1, 'location': [10, 5]},
        {'mode': 1, 'location': [10, 5]},
        {'mode': 1, 'location': [10, 5]},
        {'mode': 2, 'location': [5, 15]},
        {'mode': 2, 'location': [5, 15]},
        {'mode': 2, 'location': [5, 15]},
    ],
    #Number of agents
    'nagents': 5,
    # 'agents': [{'source','target','time_source','time_target','mode'}]
}

####### DEFINITION OF CLASSES (City, Staion, Bike, Agent) ######
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
        #Takes data of stations and goes one by one adjudicating the data to the station objects 
        for station_id, station_data in enumerate(self.data['stations']): 
            station = Station(self.env, station_id)  #Takes data of stations and goes one by one adjudicating the data to the station objects (that now have an id)
            station.set_capacity(station_data['capacity']) #asjudicating data
            station.set_location(np.array(station_data['location'])) # " np.array() helps to structure data ???
            station.init_station() #initialize that station (resource and container)
            self.stations.append(station) #Adds station to the staions array in city

    def init_bikes(self):
        for bike_id, bike_data in enumerate(self.data['bikes']): #There is not Dockless 1 and Autonomous 1, they share ids !
            mode = bike_data['mode'] #Takes the mode 
            if mode == 0:
                bike = StationBike(self.env, bike_id) 
                station_id = bike_data['station'] 
                self.stations[station_id].push_bike(bike_id) #Saves the bike in the station
                bike.set_station(station_id)  # saves the station in the bike 
                bike.set_location(self.stations[station_id].location)  #Saves the location of the station as its location
            elif mode == 1:
                bike = DocklessBike(self.env, bike_id) #creates object of class Dockless Bike with the env and the id as imput
                bike.set_location(np.array(bike_data['location'])) #initial location is given, so it takes it and saves it
            elif mode == 2:
                bike = AutonomousBike(self.env, bike_id) #creates object of class Autonomous Bike with the env and the id as imput
                bike.set_location(np.array(bike_data['location'])) #initial location is given, so it takes it and saves it
            self.bikes.append(bike) #Adds bike to the array of Bikes in city

    def init_agents(self):
        for agent_id in range(self.data['nagents']): #here the only input is the number of agents
            mode = np.random.randint(0,2) #assigns a random mode
            # mode = 2
            #Creates a different class of agent depending in the mode
            if mode == 0:
                agent = StationAgent(self.env, agent_id)
            elif mode == 1:
                agent = DocklessAgent(self.env, agent_id)
            elif mode == 2:
                agent = AutonomousAgent(self.env, agent_id)
            agent.set_data(self.data['grid'], self.stations, self.bikes) #To 'know' the city / It needs this data to operate # TO-DO ???¿
            agent.start() #Defines structure for location, bike id and event setup ?
            self.agents.append(agent) #Adds the agent to the array of agents in city


class Station:

    def __init__(self, env, station_id): #constructor
        self.env = env
        self.station_id = station_id

        self.location = None
        self.capacity = None
        self.bikes = []

        self.history = []
        self.init_state()

    def init_state(self):
        state_keys = ['time', 'bikes', 'nbikes']
        self.state = dict.fromkeys(state_keys)

    def init_station(self): #parameters that help to manage the station
        self.resource = simpy.Resource(self.env, capacity=1) # Put some order in case 2 arrite at the same time Do we need this ? If all slots are taken, requests are enqueued. Once a usage request is released, a pending request will be triggered
        self.container = simpy.Container(self.env, self.capacity, init=0) #It supports requests to put or get matter into/from the container

    def set_location(self, location):  #takes location defined in City class definition and saves it
        self.location = location

    def set_capacity(self, capacity): #takes capacity defined in City class definition and saves it
        self.capacity = capacity

    def has_bikes(self):
        return self.container.level > 0

    def has_docks(self):
        return self.capacity - self.container.level > 0

    def empty(self):
        return self.container.level == 0

    def full(self):
        return self.container.level == self.capacity

    def choose_bike(self):  # Selects any bike (Random package)
        return random.choice(self.bikes)

    def pull_bike(self, bike_id):
        if self.has_bikes(): #Check that it has bikes
            self.container.get(1) #Counts that there is one less
            self.bikes.remove(bike_id) #removes that bike from the list
            self.save_state() #saves time/bikes/nbikes in history -> FORMAT? and then init_state??
            self.print_info() #prints time/station/nbikes/capacity
        else:
            print('[%.2f] Station %d has no bikes available' %
              (self.env.now, self.station_id))

    def push_bike(self, bike_id):
        if self.has_docks(): #check that there are docks available
            self.container.put(1) #add one item 
            self.bikes.append(bike_id) #add the bike's id
            self.save_state() #saves time/bikes/nbikes in history
            self.print_info() #prints time/station/nbikes/capacity
        else:
            print('[%.2f] Station %d has no docks available' %
              (self.env.now, self.station_id))

    def save_state(self): #FORMAT?
        # print(self.station_id, np.round(self.env.now), self.bikes, len(self.bikes))
        self.state['time'] = np.round(self.env.now)
        self.state['bikes'] = self.bikes.copy()
        self.state['nbikes'] = len(self.bikes)
        self.history.append(self.state)
        self.init_state()

    def print_info(self): #Prints time, station, and nbikes/capacity
        print('[%.2f] Station %d has %d bikes out of %d' %
              (self.env.now, self.station_id, self.container.level, self.capacity))


class Bike:
    def __init__(self, env, bike_id): #constructor
        self.env = env
        self.bike_id = bike_id

        self.agent_id = None
        self.location = None

        self.history = []
        self.print = False

    def init_state(self):
        state_keys = ['agent_id', 'mode',
                      'station_pull', 'time_pull', 'station_push', 'time_push',
                      'location_unlock', 'time_unlock', 'location_drop', 'time_drop',
                      'location_call', 'time_call', 'location_meet', 'time_meet']
        self.state = dict.fromkeys(state_keys)

    def set_agent(self, agent_id):
        self.agent_id = agent_id

    def set_location(self, location):
        self.location = location

    def pop_agent(self):
        self.agent_id = None

    def rented(self):
        return self.agent_id is not None

    def dist(self, a, b):
        return np.linalg.norm(a - b)

    def ride(self, location):
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)
        self.location = location


class StationBike(Bike):
    def __init__(self, env, bike_id):
        super().__init__(env, bike_id)
        self.station_id = None
        self.init_state()

    def init_state(self):
        state_keys = ['agent_id', 'station_pull', 'time_pull', 'station_push', 'time_push']
        self.state = dict.fromkeys(state_keys)

    def save_state(self):
        self.history.append(self.state)
        self.init_state()

    def set_station(self, station_id):
        self.station_id = station_id

    def pop_station(self):
        self.station_id = None

    def register_pull(self, agent_id):
        if self.print:
            print('[%.2f] Bike %d pulled from station %d by agent %d' %
                    (self.env.now, self.bike_id, self.station_id, agent_id))

        self.state['agent_id'] = agent_id
        self.state['station_pull'] = self.station_id
        self.state['time_pull'] = np.round(self.env.now, 2)
        self.set_agent(agent_id)
        self.pop_station()

    def register_push(self, station_id):
        if self.print:
            print('[%.2f] Bike %d pushed on station %d by agent %d' %
                    (self.env.now, self.bike_id, station_id, self.agent_id))

        self.state['station_push'] = station_id
        self.state['time_push'] = np.round(self.env.now, 2)
        self.save_state()
        self.pop_agent()
        self.set_station(station_id)
    
    def docked(self):
        return self.station_id is not None

class DocklessBike(Bike):
    def __init__(self, env, bike_id):
        super().__init__(env, bike_id)        
        self.init_state()

    def init_state(self):
        state_keys = ['agent_id', 'location_unlock', 'time_unlock', 'location_lock', 'time_lock']
        self.state = dict.fromkeys(state_keys)

    def save_state(self):
        self.history.append(self.state)
        self.init_state()

    def unlock(self, agent_id):
        self.set_agent(agent_id)
        self.state['agent_id'] = agent_id
        self.state['time_unlock'] = np.round(self.env.now, 2)
        self.state['location_unlock'] = self.location

        if self.print:
            print('[%.2f] Dockless bike %d unlocked by agent %d on location [%.2f, %.2f]' %
                    (self.env.now, self.bike_id, agent_id, *self.location))

    def lock(self):
        if self.print:
            print('[%.2f] Dockless bike %d locked by agent %d on location [%.2f, %.2f]' %
                    (self.env.now, self.bike_id, self.agent_id, *self.location))

        self.state['location_lock'] = self.location
        self.state['time_lock'] = np.round(self.env.now, 2)
        self.pop_agent()
        self.save_state()

class AutonomousBike(Bike):
    def __init__(self, env, bike_id):
        super().__init__(env, bike_id)
        self.init_state()

    def init_state(self):
        state_keys = ['agent_id', 'location_call', 'time_call', 'location_meet', 'time_meet', 'location_drop', 'time_drop']
        self.state = dict.fromkeys(state_keys)

    def save_state(self):
        self.history.append(self.state)
        self.init_state()

    def call(self, agent_id):
        self.set_agent(agent_id)
        self.state['agent_id'] = agent_id
        self.state['time_call'] = np.round(self.env.now, 2)
        self.state['location_call'] = self.location

        if self.print:
            print('[%.2f] Autonomous bike %d called by agent %d' %
                    (self.env.now, self.bike_id, agent_id))

    def autonomous_move(self, location):
        if self.print:
            print('[%.2f] Autonomous bike %d moving from [%.2f, %.2f] to [%.2f, %.2f]' %
                    (self.env.now, self.bike_id, *self.location, *location))
        
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)

        if self.print:
            print('[%.2f] Autonomous bike %d moved from [%.2f, %.2f] to [%.2f, %.2f]' %
                    (self.env.now, self.bike_id, *self.location, *location))

        self.location = location
        self.state['location_meet'] = self.location
        self.state['time_meet'] = np.round(self.env.now, 2)

    def drop(self):
        if self.print:
            print('[%.2f] Autonomous bike %d dropped by agent %d on location [%.2f, %.2f]' %
                    (self.env.now, self.bike_id, self.agent_id, *self.location))

        self.state['location_drop'] = self.location
        self.state['time_drop'] = np.round(self.env.now, 2)
        self.pop_agent()
        self.save_state()

class Agent:

    def __init__(self, env, agent_id):
        self.env = env
        self.agent_id = agent_id
        self.grid = None
        self.stations = None
        self.bikes = None

        self.print = True
        self.history = []
        self.init_state()

    def init_state(self):
        state_keys = ['source', 'target', 'time_source', 'time_target', 'bike_id', 'mode',
                      'source_history', 'target_history','dockless_history', 'autonomous_history']
        self.state = dict.fromkeys(state_keys)

    def set_data(self, grid, stations, bikes):
        self.grid = grid
        self.stations = stations
        self.bikes = bikes

    def start(self):
        self.location = None
        self.bike_id = None
        self.event_setup_task = self.env.event()
        
    def process(self):
        # 0-Setup
        self.setup_task()
        yield self.event_setup_task

        # 1-Init on source
        yield self.env.process(self.init_agent())

    def setup_task(self):
        # self.source = self.random_location()
        # self.target = self.random_location()
        self.source = np.array([0, 0]) + np.random.normal(0,1, size=2)
        self.target = np.array([100, 100]) + np.random.normal(0,1, size=2)

        self.time_source = np.round(self.random_time(), 2)
        self.time_target_desired = np.round(self.time_source + self.random_time(), 2)

        self.event_setup_task.succeed()

        if self.print:
            print('[%.2f] Agent %d task created' %
                  (self.env.now, self.agent_id))
            print('[%.2f] Agent %d source location: (%.2f, %.2f) at %.2f' %
                  (self.env.now, self.agent_id, *self.source, self.time_source))
            print('[%.2f] Agent %d target location: (%.2f, %.2f) at %.2f' %
                  (self.env.now, self.agent_id, *self.target, self.time_target_desired))

    def init_agent(self):
        yield self.env.timeout(self.time_source)
        self.location = self.source
        if self.print:
            print('[%.2f] Agent %d initialized at location [%.2f, %.2f]' %
                  (self.env.now, self.agent_id, *self.location))

    def random_location(self):
        x = np.random.randint(*self.grid['xlim'])
        y = np.random.randint(*self.grid['ylim'])
        return np.array([x, y])

    def random_time(self):
        return np.random.randint(0,10) # 10

    def dist(self, a, b):
        return np.linalg.norm(a - b)

    def walk_to(self, location):
        distance = self.dist(self.location, location)
        yield self.env.timeout(distance)
        self.location = location

        if self.print:
            print('[%.2f] Agent %d walked to location [%.2f, %.2f]' %
                  (self.env.now, self.agent_id, *location))

    def ride_bike_to(self, location):
        if self.print:
            print('[%.2f] Agent %d heads from location [%.2f, %.2f] to location [%.2f, %.2f] on bike %d' %
                  (self.env.now, self.agent_id, *self.location, *location, self.bike_id))

        bike = self.bikes[self.bike_id]
        yield self.env.process(bike.ride(location))

        if self.print:
            print('[%.2f] Agent %d reached from location [%.2f, %.2f] to location [%.2f, %.2f] on bike %d' %
                  (self.env.now, self.agent_id, *self.location, *location, self.bike_id))

        self.location = location

class StationAgent(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)
        self.init_state()

    def init_state(self):
        state_keys = ['source', 'target', 'time_source', 'time_target', 'bike_id', 'station_history']
        self.state = dict.fromkeys(state_keys)

    def save_state(self):
        self.state['source'] = self.source.tolist()
        self.state['target'] = self.target.tolist()
        self.state['time_source'] = self.time_source
        self.state['time_target'] = self.time_target
        self.state['bike_id'] = self.bike_id
        self.state['station_history'] = self.station_history
        self.history.append(self.state)
        self.init_state()

    def save_station_history(self, aim):
        history = {
            'aim': aim,
            'station_id': self.station_id,
            'time_select_station': self.time_select_station,
            'time_in_station': self.time_in_station,
            'time_interact_bike': self.time_interact_bike
        }
        self.station_history.append(history)

    def start(self):
        super().start()

        # STATION-BASED
        self.station_id = None
        self.event_select_station = self.env.event()
        self.event_interact_bike = self.env.event()
        self.visited_stations = []
        self.station_history = []

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on source
        yield self.env.process(super().process())

        self.event_interact_bike = self.env.event()
        while not self.event_interact_bike.triggered:
            # 2-Select source station
            self.select_station(aim='source')

            # 3-Walk to source station
            yield self.event_select_station
            station = self.stations[self.station_id]
            yield self.env.process(self.walk_to(station.location))
            self.time_in_station = np.round(self.env.now, 2)

            # 4-Pull bike
            yield self.env.process(self.interact_bike(action='pull'))
            self.save_station_history(aim='source')

        self.event_interact_bike = self.env.event()
        while not self.event_interact_bike.triggered:
            # 5-Select target station
            self.select_station(aim='target')

            # 6-Ride bike
            yield self.event_select_station
            station = self.stations[self.station_id]
            yield self.env.process(self.ride_bike_to(station.location))
            self.time_in_station = np.round(self.env.now, 2)

            # 7-Push bike
            yield self.env.process(self.interact_bike(action='push'))
            self.save_station_history(aim='target')

        # 8-Walk to target
        yield self.env.process(self.walk_to(self.target))
        self.time_target = np.round(self.env.now, 2)

        # 9-Save state
        self.save_state()

        # 10-Finish
        yield self.env.timeout(10)
        if self.print:
            print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))
    
    # STATION BASED
   
    def update_station_info(self, location):
        values = []
        for station in self.stations:
            station_id = station.station_id
            has_bikes = station.has_bikes()
            has_docks = station.has_docks()
            visited = station_id in self.visited_stations
            distance = self.dist(location, station.location) 
            walkable = distance < WALK_RADIUS
            values.append((station_id, has_bikes, has_docks,
                           visited, distance, walkable))
        labels = ['station_id', 'has_bikes', 'has_docks',
                  'visited', 'distance', 'walkable']
        types = [int, int, int,
                 int, float, int]
        dtype = list(zip(labels, types))
        self.station_info = np.array(values, dtype=dtype)

    def select_station(self, aim):
        self.event_select_station = self.env.event()
        location = self.location if aim == 'source' else self.target ###?????? aim== source
        self.update_station_info(location)
        for e in np.sort(self.station_info, order='distance'):
            if aim == 'source':
                valid = e['has_bikes'] and not e['visited'] and e['walkable']
            else:
                valid = e['has_docks'] and not e['visited'] and e['walkable']
            if valid:
                self.station_id = e['station_id']
                self.visited_stations.append(self.station_id)
                self.event_select_station.succeed()
                self.time_select_station = np.round(self.env.now, 2)
                if self.print:
                    print('[%.2f] Agent %d selected %s station %d' %
                          (self.env.now, self.agent_id, aim, self.station_id))
                break
        if not self.event_select_station.triggered:
            print("estoy in da shit")
            # if we already pulled a bike, we are f***ed

            # call taxi / uber
            # walk to random station
            # walk towards target
            # wait and try again
            # change mode and start again
            # increase walkable distance
            # create new bike
            # stop
        
    def interact_bike(self, action):
        station = self.stations[self.station_id]
        valid = station.has_bikes() if action == 'pull' else station.has_docks()
        if valid:
            if action == 'pull':
                self.bike_id = station.choose_bike()
                self.bikes[self.bike_id].register_pull(self.agent_id)
                station.pull_bike(self.bike_id) #HERE prints state of station
            else:
                self.bikes[self.bike_id].register_push(self.station_id)
                station.push_bike(self.bike_id)

            self.event_interact_bike.succeed()
            self.time_interact_bike = np.round(self.env.now, 2)
            if self.print: # AND HERE the action, the order is counfusing
                print('[%.2f] Agent %d %sed bike %d on station %d' %
                      (self.env.now, self.agent_id, action, self.bike_id, self.station_id))
            yield self.env.timeout(1)
        else:
            self.time_interact_bike = None
            if self.print:
                print('[%.2f] Station %d has zero %s available' %
                       (self.env.now, self.station_id, 'bikes' if action == 'pull' else 'docks'))
            yield self.env.timeout(3)

class DocklessAgent(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)
        self.init_state()

    def init_state(self):
        state_keys = ['source', 'target', 'time_source', 'time_target', 'bike_id', 'dockless_history']
        self.state = dict.fromkeys(state_keys)

    def save_state(self):
        self.state['source'] = self.source.tolist()
        self.state['target'] = self.target.tolist()
        self.state['time_source'] = self.time_source
        self.state['time_target'] = self.time_target
        self.state['bike_id'] = self.bike_id
        self.state['dockless_history'] = self.dockless_history
        self.history.append(self.state)
        self.init_state()

    def save_dockless_history(self):
        history = {
            'dockless_bike_id': self.dockless_bike_id,
            'time_select_bike': self.time_select_bike,
            'time_in_dockless_bike': self.time_in_dockless_bike,
            'time_unlock_bike': self.time_unlock_bike
        }
        self.dockless_history.append(history)

    def start(self):
        super().start()

        # DOCKLESS
        self.dockless_bike_id = None
        self.dockless_history = []

        self.event_select_dockless_bike = self.env.event()
        self.event_unlock_bike = self.env.event()

        self.env.process(self.process())

    def process(self):
        # 0-Setup
        # 1-Init on source
        yield self.env.process(super().process())

        while not self.event_unlock_bike.triggered:
            # 2-Select dockless bike
            self.select_dockless_bike()

            # 3-Walk to dockless bike
            yield self.event_select_dockless_bike
            dockless_bike = self.bikes[self.dockless_bike_id]
            yield self.env.process(self.walk_to(dockless_bike.location))
            self.time_in_dockless_bike = np.round(self.env.now, 2)

            # 4-Unlock bike
            yield self.env.process(self.unlock_bike())
            self.save_dockless_history()

        # 5-Ride bike
        yield self.env.process(self.ride_bike_to(self.target))

        # 6-Drop bike
        self.lock_bike()
        self.time_target = np.round(self.env.now, 2)

        # 7-Save state
        self.save_state()

        # 8-Finish
        yield self.env.timeout(10)
        if self.print:
            print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))


    def update_bike_info(self):
        values = []
        for bike in self.bikes:
            if isinstance(bike, DocklessBike):
                bike_id = bike.bike_id
                rented = bike.rented()
                distance = self.dist(self.location, bike.location)
                walkable = distance < WALK_RADIUS
                values.append((bike_id, rented, distance, walkable))
        labels = ['bike_id', 'rented', 'distance', 'walkable']
        types = [int, int, float, int]
        dtype = list(zip(labels, types))
        self.bike_info = np.array(values, dtype=dtype)

    def select_dockless_bike(self):
        self.event_select_dockless_bike = self.env.event()
        self.update_bike_info()
        for e in np.sort(self.bike_info, order='distance'):
            # print(e)
            valid = not e['rented'] and e['walkable']
            if valid:
                self.dockless_bike_id = e['bike_id']
                self.event_select_dockless_bike.succeed()
                self.time_select_bike = np.round(self.env.now, 2)
                if self.print:
                    print('[%.2f] Agent %d selected dockless bike %d' %
                          (self.env.now, self.agent_id, self.dockless_bike_id))
                break
        if not self.event_select_dockless_bike.triggered:
            print("estoy in da shit")
            # call taxi / uber
            # walk towards target
            # wait and try again
            # change mode and start again
            # increase walkable distance
            # create new bike
            # stop


    def unlock_bike(self):
        dockless_bike = self.bikes[self.dockless_bike_id]
        if not dockless_bike.rented():
            yield self.env.timeout(1)
            self.bike_id = dockless_bike.bike_id
            dockless_bike.unlock(self.agent_id)
            #HERE IT DOESNT SAVE THAT IT HAS BEEN RENTED
            self.event_unlock_bike.succeed()
            self.time_unlock_bike = np.round(self.env.now, 2)
            if self.print:
                print('[%.2f] Agent %d unlocked bike %d' %
                      (self.env.now, self.agent_id, self.bike_id))
        else:
            yield self.env.timeout(3)
            self.time_unlock_bike = None
            if self.print:
                print('[%.2f] Bike %d has already been rented' %
                      (self.env.now, self.dockless_bike_id))

    def lock_bike(self):
        bike = self.bikes[self.bike_id]
        bike.lock()

        if self.print:
            print('[%.2f] Agent %d locked bike %d' %
                  (self.env.now, self.agent_id, self.bike_id))

class AutonomousAgent(Agent):
    def __init__(self, env, agent_id):
        super().__init__(env, agent_id)
        self.init_state()

    def init_state(self):
        state_keys = ['source', 'target', 'time_source', 'time_target', 'bike_id', 'autonomous_history']
        self.state = dict.fromkeys(state_keys)

    def save_state(self):
        self.state['source'] = self.source.tolist()
        self.state['target'] = self.target.tolist()
        self.state['time_source'] = self.time_source
        self.state['time_target'] = self.time_target
        self.state['bike_id'] = self.bike_id
        self.state['autonomous_history'] = {
            'time_call_bike': self.time_call_bike,
            'time_meet_bike': self.time_meet_bike
        }
        self.history.append(self.state)
        self.init_state()


    def start(self):
        super().start()

        # AUTONOMOUS
        self.event_call_autonomous_bike = self.env.event()
        self.autonomous_history = []

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
        self.time_meet_bike = np.round(self.env.now, 2)

        # 4-Ride bike
        yield self.env.process(self.ride_bike_to(self.target))

        # 5-Drop bike
        self.drop_bike()
        self.time_target = np.round(self.env.now, 2)

        # 6-Save state
        self.save_state()

        # 7-Finish
        yield self.env.timeout(10)
        if self.print:
            print('[%.2f] Agent %d working' % (self.env.now, self.agent_id))


    def update_bike_info(self):
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

    def call_autonomous_bike(self):
        self.event_call_autonomous_bike = self.env.event()
        self.update_bike_info()
        for e in np.sort(self.bike_info, order='distance'):
            # print(e)
            valid = not e['rented'] and e['walkable']
            if valid:
                self.bike_id = e['bike_id']
                self.bikes[self.bike_id].call(self.agent_id)
                self.event_call_autonomous_bike.succeed()
                self.time_call_bike = np.round(self.env.now, 2)
                if self.print:
                    print('[%.2f] Agent %d called autonomous bike %d' %
                          (self.env.now, self.agent_id, self.bike_id))
                break
        if not self.event_call_autonomous_bike.triggered:
            print("estoy in da shit")
            # call taxi / uber
            # walk to random station
            # walk towards target
            # wait and try again
            # change mode and start again
            # increase walkable distance
            # create new bike
            # stop

    def drop_bike(self):
        bike = self.bikes[self.bike_id]
        bike.drop()

        if self.print:
            print('[%.2f] Agent %d dropped bike %d' %
                  (self.env.now, self.agent_id, self.bike_id))



env = simpy.Environment()
city = City(env, data)
env.run(until=1000)


# %%

stations = []
for station_id, station in enumerate(city.stations):
    df = pd.DataFrame(station.history).assign(station_id=station_id)
    stations.append(df)
df_stations = pd.concat(stations).set_index('station_id').reset_index()


bikes = []
for bike_id, bike in enumerate(city.bikes):
    bike_type = type(bike).__name__
    df = pd.DataFrame(bike.history).assign(bike_id=bike_id, bike_type=bike_type)
    bikes.append(df)
df_bikes = pd.concat(bikes, sort=False).set_index('bike_id').reset_index()


agents = []
for agent_id, agent in enumerate(city.agents):
    agent_type = type(agent).__name__
    df = pd.DataFrame(agent.history).assign(agent_id=agent_id, agent_type=agent_type)
    agents.append(df)

df_agents = pd.concat(agents).set_index('agent_id').reset_index()