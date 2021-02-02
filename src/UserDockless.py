import logging


class UserDockless:
    id_count = -1

    def __init__(self, env, graph, ui, config, origin, destination, departure_time, target_time):
        self.next_id()
        self.id = UserDockless.id_count

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
        UserDockless.id_count += 1

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

        self.event_unlock_bike = self.env.event()
        while not self.event_unlock_bike.triggered:

            # 2-Select dockless bike
            self.bike_id, bike_location = self.select_dockless_bike(self.location)

            if self.bike_id is None:
                logging.info("[%.2f] User %d  will not make the trip" % (self.env.now, self.id))
                return

            logging.info("[%.2f] User %d selected dockless bike %d" % (self.env.now, self.id, self.bike_id))

            # 3-Walk to dockless bike
            yield self.env.process(self.walk_to(bike_location))

            # 4-Unlock bike
            yield self.env.process(self.unlock_bike())

        # 5-Ride bike
        yield self.env.process(self.ride_bike_to(self.destination))

        # 6-Lock bike
        yield self.env.process(self.lock_bike())

        # 7-Save state
        # self.save_state()

        # # 8-Finish
        yield self.env.timeout(10)
        logging.info("[%.2f] User %d arrived to final location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat))

    def select_dockless_bike(self, location):
        return self.ui.select_dockless_bike(location)

    def unlock_bike(self):
        if not self.ui.bike_busy(self.bike_id):
            yield self.env.timeout(1)
            self.ui.bike_unlock(self.bike_id, self.id)
            logging.info("[%.2f] User %d unlocked bike %d" % (self.env.now, self.id, self.bike_id))
            self.event_unlock_bike.succeed()
        else:
            yield self.env.timeout(3)
            logging.info("[%.2f] User %d, bike %d has already been rented. Looking for another one." % (self.env.now, self.id, self.bike_id))
            self.bike_id = None

    def lock_bike(self):
        yield self.env.timeout(1)
        self.ui.bike_lock(self.bike_id)
        logging.info("[%.2f] User %d locked bike %d" % (self.env.now, self.id, self.bike_id))
