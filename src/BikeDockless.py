class BikeDockless:
    id_count = -1

    def __init__(self, env, graph, config):
        self.next_id()
        self.id = BikeDockless.id_count

        self.env = env
        self.graph = graph
        self.config = config

        self.location = None
        self.user = None
        self.busy = False  # reserved, driving autonomously, in use...

        self.RIDING_SPEED = config["RIDING_SPEED"] / 3.6  # m/s

    def next_id(self):
        BikeDockless.id_count += 1

    def set_location(self, location):
        self.location = location
        self.update_node()

    def update_node(self):
        self.location.node = self.graph.network.get_node_ids([self.location.lon], [self.location.lat])[0]

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
        self.set_location(destination)

    def dist(self, a, b):
        return self.graph.shortest_path_length(a, b)

    def unlock(self, user_id):
        self.update_user(user_id)
        self.busy = True

    def lock(self):
        self.delete_user()
        self.busy = False
