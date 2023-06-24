class BikeStation:
    id_count = -1

    def __init__(self, env, graph, config):
        self.next_id()
        self.id = BikeStation.id_count

        self.env = env
        self.graph = graph
        self.config = config

        self.location = None
        self.user = None
        self.busy = False  # reserved, driving autonomously, in use...
        self.station_id = None

        self.RIDING_SPEED = config["RIDING_SPEED"] / 3.6  # m/s

    def next_id(self):
        BikeStation.id_count += 1

    def set_location(self, location):
        self.location = location

    def update_user(self, user_id):
        self.user = user_id

    def delete_user(self):
        self.user = None

    def vacant(self):
        if self.user is None:
            return True

    def ride(self, destination):
        distance = self.dist(self.location, destination)
        time = distance / self.RIDING_SPEED
        yield self.env.timeout(time)
        self.location = destination

    def dist(self, a, b):
        return self.graph.shortest_path_length(a, b)

    def attach_station(self, station_id):
        self.station_id = station_id

    def detach_station(self):
        self.station_id = None

    def register_unlock(self, user_id):
        self.update_user(user_id)
        self.detach_station()
        self.busy = True

    def register_lock(self, station_id):
        self.delete_user()
        self.attach_station(station_id)
        self.busy = False

    def docked(self):
        return self.station_id is not None
