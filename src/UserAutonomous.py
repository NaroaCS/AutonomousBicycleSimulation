import logging
from .UserTrip import UserTrip


class UserAutonomous:
    id_count = -1

    def __init__(
        self, env, graph, ui, config, results, origin, destination, departure_time, target_time,
    ):
        self.next_id()
        self.id = UserAutonomous.id_count

        self.env = env
        self.graph = graph
        self.ui = ui
        self.config = config
        self.results = results
        self.user_trip = UserTrip()

        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.target_time = target_time

        self.location = None
        self.bike_id = None
        self.bike_location = None
        self.time_wait = None
        self.time_ride = None

        self.WALKING_SPEED = config["WALKING_SPEED"] / 3.6  # m/s

    @classmethod
    def reset(cls):
        UserAutonomous.id_count = -1

    def next_id(self):
        UserAutonomous.id_count += 1

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
        return self.graph.get_shortest_path_length(a, b)

    def start(self):
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

        # 2-Call autonomous bike
        self.bike_id, self.bike_location = self.call_autonomous_bike(self.location)

        if self.bike_id is None:
            logging.info("[%.2f] User %d will not make the trip" % (self.env.now, self.id))
            return

        logging.info("[%.2f] User %d was assigned the autonomous bike %d" % (self.env.now, self.id, self.bike_id))

        # 3-Wait for autonomous bike
        yield self.env.process(self.autonomous_drive())
        self.time_wait = self.env.now - self.departure_time
        yield self.env.process(self.unlock_bike())

        # 4-Ride bike
        yield self.env.process(self.ride_bike_to(self.destination))

        # 5-Lock bike
        yield self.env.process(self.lock_bike())

        # 6-Finish
        # yield self.env.timeout(0)
        # TODO: estimate travel from building to nearest node
        logging.info("[%.2f] User %d arrived to final destination" % (self.env.now, self.id))

        # 7-Charge bike if low battery
        yield self.env.process(self.charge_bike())

        self.time_ride = self.env.now - self.departure_time
        # 8-Save state
        self.save_user_trip()

    def autonomous_drive(self):
        yield self.env.process(self.ui.autonomous_drive(self.bike_id, self.location, self.id))

    def call_autonomous_bike(self, location):
        return self.ui.call_autonomous_bike(location)

    def charge_bike(self):
        yield self.env.process(self.ui.bike_charge(self.bike_id))

    def unlock_bike(self):
        yield self.env.timeout(1)
        self.ui.bike_unlock(self.bike_id, self.id)
        logging.info("[%.2f] User %d unlocked bike %d" % (self.env.now, self.id, self.bike_id))

    def lock_bike(self):
        yield self.env.timeout(1)
        self.ui.bike_lock(self.bike_id)
        logging.info("[%.2f] User %d locked bike %d" % (self.env.now, self.id, self.bike_id))

    def save_user_trip(self):
        self.user_trip.set("user_id", self.id)
        self.user_trip.set("bike_id", self.bike_id)
        self.user_trip.set("mode", 2)

        self.user_trip.set("time_departure", self.departure_time, 0)
        self.user_trip.set("time_target", self.target_time, 0)
        self.user_trip.set("time_ride", self.time_ride, 0)
        self.user_trip.set("time_wait", self.time_wait, 0)

        self.user_trip.set("origin_lon", self.origin.lon, 5)
        self.user_trip.set("origin_lat", self.origin.lat, 5)
        self.user_trip.set("destination_lon", self.destination.lon, 5)
        self.user_trip.set("destination_lat", self.destination.lat, 5)

        self.user_trip.set("bike_lon", self.bike_location.lon)
        self.user_trip.set("bike_lat", self.bike_location.lat)

        self.results.add_user_trip(self.user_trip)
