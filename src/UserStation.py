import numpy as np
import logging
from .UserTrip import UserTrip
from .BikeTrip import BikeTrip


class UserStation:
    id_count = -1

    def __init__(
        self, env, graph, ui, config, results, origin, destination, departure_time, target_time,
    ):
        self.next_id()
        self.id = UserStation.id_count
        self.env = env
        self.graph = graph
        self.ui = ui
        self.config = config
        self.results = results

        self.user_trip = UserTrip()
        self.bike_trip = BikeTrip()

        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.target_time = target_time
        self.location = None
        self.bike_id = None
        self.status = None

        self.origin_station = None
        self.destination_station = None
        self.origin_visited_stations = None
        self.destination_visited_stations = None

        self.magic_bike = 0
        self.magic_dock = 0

        self.time_walk_origin = None
        self.time_ride = None
        self.time_walk_destination = None

        self.WALKING_SPEED = config["WALKING_SPEED"] / 3.6
        self.MAGIC_BETA = config["MAGIC_BETA"]

    @classmethod
    def reset(cls):
        UserStation.id_count = -1

    def next_id(self):
        UserStation.id_count += 1

    def walk_to(self, location):
        distance = self.dist(self.location, location)
        time = distance / self.WALKING_SPEED
        yield self.env.timeout(time)
        logging.info("[%.2f] User %d walked from [%.4f, %.4f] to location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat, location.lon, location.lat,))
        self.location = location

    def ride_bike_to(self, location):
        logging.info(
            "[%.2f] User %d biking with bike %d from [%.4f, %.4f] to location [%.4f, %.4f]" % (self.env.now, self.id, self.bike_id, self.location.lon, self.location.lat, location.lon, location.lat,)
        )
        yield self.env.process(self.ui.bike_ride(self.bike_id, location))
        self.location = location

    def dist(self, a, b):
        return self.graph.shortest_path_length(a, b)

    def start(self):
        self.env.process(self.process())

    def init_user(self):
        yield self.env.timeout(self.departure_time)
        self.location = self.origin
        # print("[%.2f] User %d  departure time: %.4f " % (self.env.now, self.id,self.departure_time ))
        logging.info("[%.2f] User %d initialized at location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat))

    def process(self):
        visited_stations = []
        yield self.env.process(self.init_user())
        self.event_interact_bike = self.env.event()
        while not self.event_interact_bike.triggered:
            (station_id, station_location, visited_stations, any_walkable,) = self.select_start_station(self.location, visited_stations)
            if station_id is None:
                if any_walkable:
                    rand_number = np.random.randint(100)
                    if rand_number <= self.MAGIC_BETA:
                        logging.info("[%.2f] User %d  made a magic bike request" % (self.env.now, self.id))
                        (station_id, station_location, visited_stations, self.magic_bike_id, self.magic_origin_station,) = self.ui.magic_bike(self.location, visited_stations)
                    if station_id is None:
                        logging.info("[%.2f] User %d  will not make the trip" % (self.env.now, self.id))
                        self.status = "no_bikes"
                        return self.save_user_trip()
                    self.magic_bike += 1
                    # self.magic_dock = 0
                    self.magic_destination_station = station_id
                    self.save_bike_trip(magic_bike=True, magic_dock=False)
                else:
                    logging.info("[%.2f] User %d had no walkable stations" % (self.env.now, self.id))  # TODO: review
                    logging.info("[%.2f] User %d  will not make the trip" % (self.env.now, self.id))
                    self.status = "not_walkable_stations"
                    return self.save_user_trip()
            logging.info("[%.2f] User %d selected start station %d" % (self.env.now, self.id, station_id))
            yield self.env.process(self.walk_to(station_location))
            yield self.env.process(self.unlock_bike(station_id))
            # if not self.event_interact_bike.triggered:
            #     rand_number = np.random.randint(100)
            #     if rand_number <= self.MAGIC_BETA:
            #         logging.info("[%.2f] User %d  made a magic bike request" % (self.env.now, self.id))
            #         station_id, station_location, visited_stations, self.magic_bike_id, self.magic_origin_station = self.ui.magic_bike(self.location, visited_stations)

        self.origin_station = station_id
        self.origin_visited_stations = ";".join(map(str, visited_stations))
        self.time_walk_origin = self.env.now - self.departure_time
        # print("[%.2f] User %d origin walking time: %.4f " % (self.env.now, self.id,self.time_walk_origin ))
        # print("[%.2f] User %d origin walk time: %.4f =%.4f - %.4f " % (self.env.now, self.id,self.time_walk_origin, self.env.now, self.departure_time))
        self.event_interact_bike = self.env.event()
        visited_stations.clear()
        while not self.event_interact_bike.triggered:
            station_id, station_location, visited_stations = self.select_end_station(self.destination, visited_stations)
            if station_id is None:
                rand_number = np.random.randint(100)
                if rand_number <= self.MAGIC_BETA:
                    logging.info("[%.2f] User %d  made a magic dock request" % (self.env.now, self.id))
                    (station_id, station_location, visited_stations, self.magic_bike_id, self.magic_origin_station,) = self.ui.magic_dock(self.destination, visited_stations)
                if station_id is not None:
                    # self.magic_bike = 0
                    self.magic_dock += 1
                    self.magic_destination_station = station_id
                    self.save_bike_trip(magic_bike=False, magic_dock=True)
                else:
                    logging.info("[%.2f] User %d  will end at a station out of walkable distance" % (self.env.now, self.id))
                    (station_id, station_location, visited_stations,) = self.ui.notwalkable_dock(self.destination, visited_stations)
                    if station_id is None:
                        logging.info("[%.2f] User %d has no end station" % (self.env.now, self.id))
                        self.status = "no_end_station"
                        return self.save_user_trip()
            logging.info("[%.2f] User %d selected end station %d" % (self.env.now, self.id, station_id))
            yield self.env.process(self.ride_bike_to(station_location))
            yield self.env.process(self.lock_bike(station_id))
            # if station_id is not None and not self.event_interact_bike.triggered:
            #     rand_number = np.random.randint(100)
            #     if rand_number <= self.MAGIC_BETA:
            #         logging.info("[%.2f] User %d  made a magic dock request" % (self.env.now, self.id))
            #         station_id, station_location, visited_stations, self.magic_bike_id, self.magic_origin_station = self.ui.magic_dock(self.destination, visited_stations)

        self.time_ride = self.env.now - self.time_walk_origin - self.departure_time
        # print("[%.2f] User %d riding time: %.4f = %.4f - %.4f - %.4f" % (self.env.now, self.id,self.time_ride, self.env.now , self.time_walk_origin , self.departure_time ))
        yield self.env.process(self.walk_to(self.destination))
        self.time_walk_destination = self.env.now - self.time_ride - self.time_walk_origin - self.departure_time
        # print("[%.2f] User %d destination walk time: %.4f =%.4f - %.4f - %.4f -%.4f" % (self.env.now, self.id,self.time_walk_destination, self.env.now, self.time_ride,self.time_ride, self.departure_time))
        # yield self.env.timeout(10)
        logging.info("[%.2f] User %d arrived to final location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat))
        self.destination_station = station_id
        self.destination_visited_stations = ";".join(map(str, visited_stations))
        self.status = "finished"
        self.save_user_trip()

    def select_start_station(self, location, visited_stations):
        return self.ui.select_start_station(location, visited_stations)

    def select_end_station(self, destination, visited_stations):
        return self.ui.select_end_station(destination, visited_stations)

    def unlock_bike(self, station_id):
        if self.ui.station_has_bikes(station_id):
            self.bike_id = self.ui.station_choose_bike(station_id)
            self.ui.bike_register_unlock(self.bike_id, self.id)
            self.ui.station_detach_bike(station_id, self.bike_id)
            logging.info("[%.2f] User %d unlocked bike %d from station %d" % (self.env.now, self.id, self.bike_id, station_id))
            self.event_interact_bike.succeed()
        else:
            logging.info("[%.2f] User %d,station %d had zero bikes available at arrival" % (self.env.now, self.id, station_id))
        yield self.env.timeout(1)

    def lock_bike(self, station_id):
        if self.ui.station_has_docks(station_id):
            self.ui.station_attach_bike(station_id, self.bike_id)
            self.ui.bike_register_lock(self.bike_id, self.id)
            logging.info("[%.2f] User %d locked bike %d in station %d" % (self.env.now, self.id, self.bike_id, station_id))
            self.event_interact_bike.succeed()
        else:
            logging.info("[%.2f] User %d,station %d had zero docks available at arrival" % (self.env.now, self.id, station_id))
        yield self.env.timeout(1)

    def interact_bike(self, action):
        if action == "unlock":
            if self.ui.station_has_bikes(self.origin_station):
                self.bike_id = self.ui.station_choose_bike(self.origin_station)
                self.ui.bike_register_unlock(self.bike_id, self.id)
                self.ui.station_detach_bike(self.origin_station, self.bike_id)
                logging.info("[%.2f] User %d unlocked bike %d from station %d" % (self.env.now, self.id, self.bike_id, self.origin_station))
                self.event_interact_bike.succeed()
            else:
                logging.info("[%.2f] User %d,station %d had zero bikes available at arrival" % (self.env.now, self.id, self.origin_station))
        else:
            if action == "lock":
                if self.ui.station_has_docks(self.destination_station):
                    self.ui.station_attach_bike(self.destination_station, self.bike_id)
                    self.ui.bike_register_lock(self.bike_id, self.id)
                    logging.info("[%.2f] User %d locked bike %d in station %d" % (self.env.now, self.id, self.bike_id, self.destination_station,))
                    self.bike_id = None
                    self.event_interact_bike.succeed()
                else:
                    logging.info("[%.2f] User %d,station %d had zero docks available at arrival" % (self.env.now, self.id, self.destination_station))
            yield self.env.timeout(1)

    def save_user_trip(self):
        self.user_trip.set("user_id", self.id)
        self.user_trip.set("status", self.status)
        self.user_trip.set("bike_id", self.bike_id)
        self.user_trip.set("mode", 0)
        self.user_trip.set("time_departure", self.departure_time, 0)
        self.user_trip.set("time_target", self.target_time, 0)
        self.user_trip.set("time_walk_origin", self.time_walk_origin, 0)
        self.user_trip.set("time_ride", self.time_ride, 0)
        self.user_trip.set("time_walk_destination", self.time_walk_destination, 0)
        self.user_trip.set("origin_lon", self.origin.lon, 5)
        self.user_trip.set("origin_lat", self.origin.lat, 5)
        self.user_trip.set("destination_lon", self.destination.lon, 5)
        self.user_trip.set("destination_lat", self.destination.lat, 5)
        self.user_trip.set("origin_station", self.origin_station)
        self.user_trip.set("destination_station", self.destination_station)
        self.user_trip.set("origin_visited_stations", self.origin_visited_stations)
        self.user_trip.set("destination_visited_stations", self.destination_visited_stations)
        self.user_trip.set("magic_bike", self.magic_bike)
        self.user_trip.set("magic_dock", self.magic_dock)
        self.results.add_user_trip(self.user_trip)

    def save_bike_trip(self, magic_dock, magic_bike):
        self.bike_trip.set("bike_id", self.magic_bike_id)
        self.bike_trip.set("user_id", self.id)
        self.bike_trip.set("mode", 0)
        self.bike_trip.set("trip_type", 0)
        self.bike_trip.set("time_departure", self.departure_time, 0)
        self.bike_trip.set("magic_bike", magic_bike)
        self.bike_trip.set("magic_dock", magic_dock)
        self.bike_trip.set("origin_station", self.magic_origin_station)
        self.bike_trip.set("destination_station", self.magic_destination_station)
        self.results.add_bike_trip(self.bike_trip)
