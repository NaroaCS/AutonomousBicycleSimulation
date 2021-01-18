import logging

from Battery import Battery


class BikeAutonomous:
    id_count = -1

    def __init__(self, env, graph, config, ui):
        self.next_id()
        self.id = BikeAutonomous.id_count

        self.env = env
        self.graph = graph
        self.config = config
        self.ui = ui

        self.location = None
        self.user_id = None
        self.busy = False  # reserved, driving autonomously, in use...

        self.RIDING_SPEED = config["RIDING_SPEED"] / 3.6  # m/s
        self.AUTONOMOUS_SPEED = config["AUTONOMOUS_SPEED"] / 3.6  # m/s

        # We will assume that all the bikes start with a full charge
        self.BATTERY_CAPACITY = 100.0
        self.BATTERY_DISCHARGE_RATE = self.BATTERY_CAPACITY / (config["BATTERY_AUTONOMY"] * 1000)  # %/meter
        self.BATTERY_CHARGE_RATE = self.BATTERY_CAPACITY / (config["BATTERY_CHARGE_TIME"] * 3600)  # %/second  (This is 5h for 100% charge)

        self.battery = Battery(self.BATTERY_CAPACITY, self.BATTERY_CHARGE_RATE, self.BATTERY_DISCHARGE_RATE)

        self.station_id = None
        self.visited_stations = []

    def next_id(self):
        BikeAutonomous.id_count += 1

    def set_location(self, location):
        self.location = location
        self.update_node()

    def update_node(self):
        self.location.node = self.graph.network.get_node_ids([self.location.lon], [self.location.lat])[0]

    def update_user(self, user_id):
        self.user_id = user_id

    def delete_user(self):
        self.user_id = None

    def vacant(self):
        if self.user_id is None:
            return True

    def ride(self, destination):
        distance = self.dist(self.location, destination)
        time = distance / self.RIDING_SPEED
        yield self.env.timeout(time)
        self.location = destination

    def dist(self, a, b):
        return self.graph.shortest_path_length(a, b)

    def unlock(self, user_id):
        self.update_user(user_id)
        self.busy = True

    def lock(self):
        self.delete_user()
        self.busy = False

    # TODO: remove (use autonomous drive)
    def go_towards(self, destination):
        # This is for the demand prediction -> maybe it's enough with autonomous_drive()
        distance = self.dist(self.location, destination)
        time = distance / self.AUTONOMOUS_SPEED
        yield self.env.timeout(time)
        self.location = destination

    def autonomous_drive(self, destination):
        logging.info("[%.2f] Bike %d driving autonomously from [%.4f, %.4f] to location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat, destination.lon, destination.lat))
        distance = self.dist(self.location, destination)
        time = distance / self.AUTONOMOUS_SPEED
        yield self.env.timeout(time)
        self.location = destination
        logging.info("[%.2f] Bike %d drove autonomously from [%.4f, %.4f] to location [%.4f, %.4f]" % (self.env.now, self.id, self.location.lon, self.location.lat, destination.lon, destination.lat))
        self.battery.discharge(distance)
        logging.info("[%.2f] Battery level of bike %d: %.2f" % (self.env.now, self.id, self.battery.level))

    def autonomous_charge(self):
        logging.info("[%.2f] Bike %d needs to recharge. Battery level:  %.2f" % (self.env.now, self.id, self.battery.level))
        # 1-Set bike as busy
        self.busy = True
        self.event_interact_station = self.env.event()

        while not self.event_interact_station.triggered:
            # 2-Select charging station
            self.station_id, station_location, self.visited_stations = self.select_charging_station(self.location, self.visited_stations)

            if self.station_id is None:
                continue  # Will try again

            logging.info("[%.2f] Bike %d going to station %d for recharge" % (self.env.now, self.id, self.station_id))

            # 3. Drive autonomously to station
            yield self.env.process(self.autonomous_drive(station_location))

            # 4-Lock in station
            yield self.env.process(self.interact_charging_station(action="lock"))

        # 5- Battery Charging
        yield self.env.process(self.battery_charge())

        # 6- Unlock from station
        yield self.env.process(self.interact_charging_station(action="unlock"))

        # 7- Set bike as free for use again
        self.busy = False
        logging.info("[%.2f] Bike %d is charged and available again" % (self.env.now, self.id))

    def select_charging_station(self, location, visited_stations):
        return self.ui.select_charging_station(location, visited_stations)

    def interact_charging_station(self, action):
        if action == "lock":
            if self.ui.station_has_docks(self.station_id):
                self.ui.station_attach_bike(self.station_id, self.id)
                logging.info("[%.2f] Bike %d locked in charging station %d" % (self.env.now, self.id, self.station_id))
                self.event_interact_station.succeed()
            else:
                logging.info("[%.2f] Bike %d,station %d had zero docks available at arrival" % (self.env.now, self.id, self.station_id))
        elif action == "unlock":
            self.ui.station_detach_bike(self.station_id, self.id)
            logging.info("[%.2f] Bike %d unlocked from charging station %d" % (self.env.now, self.id, self.station_id))

        yield self.env.timeout(1)  # TODO: remove??

    def battery_charge(self):
        logging.info("[%.2f] Bike %d started recharging" % (self.env.now, self.id))
        time = self.battery.total_charge_time()
        yield self.env.timeout(time)
        self.battery.charge(time)
        logging.info("[%.2f] Bike %d fully charged" % (self.env.now, self.id))
