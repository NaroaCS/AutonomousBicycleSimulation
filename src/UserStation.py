import numpy as np
import logging


class UserStation:
    id_count = -1

    def __init__(self, env, graph, ui, config, origin, destination, departure_time, target_time):
        self.next_id()
        self.id = UserStation.id_count

        self.env = env
        self.graph = graph
        self.ui = ui
        self.config = config

        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.target_time = target_time

        self.location = None
        self.bike_id = None
        self.station_id = None
        # self.state = None  # None, walking,waiting,biking ..> Not used for now

        self.WALKING_SPEED = config["WALKING_SPEED"] / 3.6  # m/s
        self.MAGIC_BETA = config["MAGIC_BETA"]  # probability of getting a magic bike or dock in %

    def next_id(self):
        UserStation.id_count += 1

    def walk_to(self, location):
        distance = self.dist(self.location, location)
        time = distance / self.WALKING_SPEED
        yield self.env.timeout(time)
        logging.info("[%.2f] User %d walked from [%.4f, %.4f] to location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat, location.lon, location.lat))
        self.location = location

    def ride_bike_to(self, location):
        logging.info(
            "[%.2f] User %d biking with bike %d from [%.4f, %.4f] to location [%.4f, %.4f]" % (self.env.now, self.id, self.bike_id, self.location.lon, self.location.lat, location.lon, location.lat)
        )
        yield self.env.process(self.ui.bike_ride(self.bike_id, location))
        self.location = location

    def dist(self, a, b):
        return self.graph.shortest_path_length(a, b)

    def start(self):
        self.station_id = None
        self.visited_stations = []

        self.env.process(self.process())

    def init_user(self):
        # waits until its the hour to initialize user
        yield self.env.timeout(self.departure_time)
        self.location = self.origin
        logging.info("[%.2f] User %d initialized at location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat))

    def process(self):
        # 0-Setup

        # 1-Init on origin
        yield self.env.process(self.init_user())

        self.event_interact_bike = self.env.event()
        while not self.event_interact_bike.triggered:

            # 2-Select origin station
            self.station_id, station_location, self.visited_stations, reason = self.select_start_station(self.location, self.visited_stations)

            # TODO: Magic bikes // when to apply?
            if self.station_id is None:
                rand_number = np.random.randint(100)
                # if rand_number <= self.MAGIC_BETA:
                #     logging.info("[%.2f] User %d  made a magic bike request" % (self.env.now, self.user_id))
                #     [station, station_location, visited_stations,] = self.ui.magic_bike(self.location, self.visited_stations)
                #     self.station_id = station
                #     if station is None:
                #         logging.info("[%.2f] User %d  will not make the trip" % (self.env.now, self.id))
                #         return
                # elif rand_number > self.MAGIC_BETA:
                #     logging.info("[%.2f] User %d  will not make the trip" % (self.env.now, self.id))
                #     return
                logging.info("[%.2f] User %d  will not make the trip" % (self.env.now, self.id))
                return
            ### HOW DO WE SAVE THE MAGIC BIKES ???? ###

            logging.info("[%.2f] User %d selected start station %d" % (self.env.now, self.id, self.station_id))

            # 3-Walk to origin station
            yield self.env.process(self.walk_to(station_location))

            # 4-unlock bike
            yield self.env.process(self.interact_bike(action="unlock"))

        self.event_interact_bike = self.env.event()
        self.visited_stations.clear()  # here we should zero it because one might do a round trip

        while not self.event_interact_bike.triggered:

            # 5-Select destination station
            self.station_id, station_location, self.visited_stations = self.select_end_station(self.destination, self.visited_stations)

            # TODO: Magic bikes
            if self.station_id is None:
                rand_number = np.random.randint(100)
                # if rand_number <= self.MAGIC_BETA:
                #     logging.info("[%.2f] User %d  made a magic dock request" % (self.env.now, self.user_id))
                #     [station, station_location, visited_stations,] = self.ui.magic_dock(self.location, self.visited_stations)
                #     if station is None:
                #         logging.info("[%.2f] User %d  will end at a station out of walkable distance" % (self.env.now, self.user_id))
                #         [station, station_location, visited_stations,] = self.ui.notwalkable_dock(self.location, self.visited_stations)

                # elif rand_number > self.MAGIC_BETA:
                #     logging.info("[%.2f] User %d  will end at a station out of walkable distance" % (self.env.now, self.user_id))
                #     [station, station_location, visited_stations,] = self.ui.notwalkable_dock(self.location, self.visited_stations)
                # self.station_id = station
                logging.info("[%.2f] User %d has no end station" % (self.env.now, self.id))
                return

            ### HOW DO WE SAVE THE MAGIC docks???? ###

            logging.info("[%.2f] User %d selected end station %d" % (self.env.now, self.id, self.station_id))

            # 6-Ride bike
            yield self.env.process(self.ride_bike_to(station_location))

            # 7-lock bike
            yield self.env.process(self.interact_bike(action="lock"))

        # 8-Walk to destination
        yield self.env.process(self.walk_to(self.destination))

        # 9-Save state
        # self.save_state()

        # # 10-Finish
        yield self.env.timeout(10)
        logging.info("[%.2f] User %d arrived to final location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat))

    def select_start_station(self, location, visited_stations):
        return self.ui.select_start_station(location, visited_stations)

    def select_end_station(self, destination, visited_stations):
        return self.ui.select_end_station(destination, visited_stations)

    # TODO: separate into lock/unlock bike
    def interact_bike(self, action):
        # Check if there are still bikes(unlock)/docks(lock) at arrival

        if action == "unlock":
            if self.ui.station_has_bikes(self.station_id):
                self.bike_id = self.ui.station_choose_bike(self.station_id)
                self.ui.bike_register_unlock(self.bike_id, self.id)
                self.ui.station_detach_bike(self.station_id, self.bike_id)
                logging.info("[%.2f] User %d unlocked bike %d from station %d" % (self.env.now, self.id, self.bike_id, self.station_id))
                self.event_interact_bike.succeed()
            else:
                logging.info("[%.2f] User %d,station %d had zero bikes available at arrival" % (self.env.now, self.id, self.station_id))

        elif action == "lock":
            if self.ui.station_has_docks(self.station_id):
                self.ui.station_attach_bike(self.station_id, self.bike_id)
                self.ui.bike_register_lock(self.bike_id, self.id)
                logging.info("[%.2f] User %d locked bike %d in station %d" % (self.env.now, self.id, self.bike_id, self.station_id))
                self.bike_id = None
                self.event_interact_bike.succeed()
            else:
                logging.info("[%.2f] User %d,station %d had zero docks available at arrival" % (self.env.now, self.id, self.station_id))

        yield self.env.timeout(1)  # TODO: remove??
