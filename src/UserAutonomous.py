import logging


class UserAutonomous:
    id_count = -1

    def __init__(self, env, graph, ui, config, origin, destination, departure_time, target_time):
        self.next_id()
        self.id = UserAutonomous.id_count

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
        # self.state = None  # None, walking,waiting,biking ..> Not used for now

        self.WALKING_SPEED = config["WALKING_SPEED"] / 3.6  # m/s

    def next_id(self):
        UserAutonomous.id_count += 1

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
        self.bike_id, bike_location = self.call_autonomous_bike(self.location)

        if self.bike_id is None:
            logging.info("[%.2f] User %d will not make the trip" % (self.env.now, self.id))
            return

        logging.info("[%.2f] User %d was assigned the autonomous bike %d" % (self.env.now, self.id, self.bike_id))

        # 3-Wait for autonomous bike
        yield self.env.process(self.autonomous_drive())
        yield self.env.process(self.unlock_bike())

        # 4-Ride bike
        yield self.env.process(self.ride_bike_to(self.destination))

        # 5-Lock bike
        yield self.env.process(self.lock_bike())

        # 6-Save state
        # self.save_state()

        # 7-Finish
        yield self.env.timeout(10)
        # TODO: estimate travel from building to nearest node
        logging.info("[%.2f] User %d arrived to final destination" % (self.env.now, self.id))

        # 8-Charge bike if low battery
        yield self.env.process(self.charge_bike())

    def autonomous_drive(self):
        yield self.env.process(self.ui.autonomous_drive(self.bike_id, self.location))

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
