import numpy as np
from scipy import spatial
import logging


def sort_lists(x, y, key=0):
    tuples = zip(*sorted(zip(x, y), reverse=False, key=lambda v: v[key]))
    x, y = [list(tuple) for tuple in tuples]
    return x, y


class DataInterface:
    def __init__(self, env, graph, config):
        self.env = env
        self.graph = graph
        self.config = config

        self.stations = []
        self.bikes = []

        self.WALK_RADIUS = config["WALK_RADIUS"]
        self.AUTONOMOUS_RADIUS = config["AUTONOMOUS_RADIUS"]
        self.BATTERY_MIN_LEVEL = config["BATTERY_MIN_LEVEL"]

        self.MAGIC_MIN_BIKES = config["MAGIC_MIN_BIKES"]
        self.MAGIC_MIN_DOCKS = config["MAGIC_MIN_DOCKS"]

    def set_bikes(self, bikes):
        self.bikes = bikes

    def set_stations(self, stations):
        self.stations = stations

    def set_data(self, stations, bikes):
        self.stations = stations
        self.bikes = bikes

    def dist(self, a, b):
        return self.graph.shortest_path_length(a, b)

    def select_start_station(self, location, visited_stations):
        stations_id, distances = self.graph.shortest_path_length_stations(location)

        reason = np.zeros(3, dtype=bool)
        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_bikes = station.has_bikes()
            visited = sid in visited_stations
            walkable = dist < self.WALK_RADIUS
            if has_bikes and not visited and walkable:
                visited_stations.append(sid)
                return sid, station.location, visited_stations, None
            reason = np.logical_or(reason, [has_bikes, not visited, walkable])

        reason_idx = [i for i, r in enumerate(reason) if not r]
        print("REASON:", reason, reason_idx)
        # if not any_has_bikes:
        #     logging.info("[%.2f] No bikes available" % (self.env.now))
        # if not any_walkable:
        #     logging.info("[%.2f] Not in walkable distance" % (self.env.now))
        return None, None, visited_stations, reason_idx

    def select_end_station(self, destination, visited_stations):
        stations_id, distances = self.graph.shortest_path_length_stations(destination)

        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_docks = station.has_docks()
            visited = sid in visited_stations
            walkable = dist < self.WALK_RADIUS
            if has_docks and not visited and walkable:
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] No docks in a walkable distance" % (self.env.now))
        return None, None, visited_stations

    def magic_bike(self, location, visited_stations):
        stations_id, distances = self.graph.shortest_path_length_stations(location)

        source_station_id = None
        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_bikes = station.num_bikes > self.MAGIC_MIN_BIKES
            if has_bikes:
                source_station_id = sid
                break

        if source_station_id is None:
            logging.info("[%.2f] No stations found as source of magic bike" % (self.env.now))
            return None, None, visited_stations

        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_docks = station.num_docks > 0
            walkable = dist < self.WALK_RADIUS
            if has_docks and walkable:
                bike_id = self.station_choose_bike(source_station_id)
                self.station_detach_bike(source_station_id, bike_id)
                self.station_attach_bike(sid, bike_id)
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] No stations found as target for magic bike" % (self.env.now))
        return None, None, visited_stations
        ##### WHERE DO WE SAVE THE nº of magic trips???? #######

    def magic_dock(self, location, visited_stations):
        stations_id, distances = self.graph.shortest_path_length_stations(location)

        source_station_id = None
        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_docks = station.num_docks > self.MAGIC_MIN_DOCKS
            if has_docks:
                source_station_id = sid
                break

        if source_station_id is None:
            logging.info("[%.2f] No stations found as target of magic bike" % (self.env.now))
            return None, None, visited_stations

        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_bikes = station.num_bikes > 0
            walkable = dist < self.WALK_RADIUS
            if has_bikes and walkable:
                bike_id = self.station_choose_bike(source_station_id)
                self.station_detach_bike(source_station_id, bike_id)
                self.station_attach_bike(sid, bike_id)
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] No stations found as source for magic bike" % (self.env.now))
        return None, None, visited_stations

    def notwalkable_dock(self, destination, visited_stations):

        stations_id, distances = self.graph.shortest_path_length_stations(destination)

        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_docks = station.has_docks()
            visited = sid in visited_stations
            if has_docks and not visited:
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] ERROR: All stations with docks had been visited -> Think about changing this part of the code" % (self.env.now))
        return None, None, visited_stations

    def select_dockless_bike(self, location):

        # nearest, not busy and walkable
        import time

        # start = time.time()
        # filter by not busy
        available_bikes = [bike for bike in self.bikes if not bike.busy]
        # print("filter available", time.time()-start)
        bikes_lon = [bike.location.lon for bike in available_bikes]
        bikes_lat = [bike.location.lat for bike in available_bikes]
        locations = np.array((bikes_lon, bikes_lat)).transpose()
        # print("get available locations", time.time()-start)

        # start = time.time()
        # create kd-tree and find k nearest
        kdtree = spatial.KDTree(locations, leafsize=50)  # , compact_nodes=False, balanced_tree=False)
        # print("create kd-tree", time.time()-start)
        k = min(10, len(available_bikes))
        d, bikes_id = kdtree.query(location.get_loc(), k)
        # print("query kd-tree", time.time()-start)

        # start = time.time()
        # get nodes in graph and estimate shortest path lengths
        user_node = location.node
        bikes_nodes = [available_bikes[i].location.node for i in bikes_id]
        # print("get nodes", time.time()-start)
        distances = self.graph.network.shortest_path_lengths(np.tile(user_node, k), bikes_nodes)
        bikes_id, distances = sort_lists(bikes_id, distances, 1)
        # print("shortest path", time.time()-start)

        # look for walkable ones
        for bid, dist in zip(bikes_id, distances):
            bike = available_bikes[bid]
            walkable = dist < self.WALK_RADIUS
            if walkable:
                return bike.id, bike.location

        logging.info("[%.2f] No bikes in walkable distance" % (self.env.now))
        return None, None

    def select_charging_station(self, location, visited_stations):
        # has docks and not visited
        stations_id, distances = self.graph.shortest_path_length_stations(location)

        for sid, dist in zip(stations_id, distances):
            station = self.stations[sid]
            has_docks = station.has_docks()
            visited = sid in visited_stations
            if has_docks and not visited:
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] No charging stations with available space that have not been visited yet" % (self.env.now))
        return None, None, visited_stations

    def call_autonomous_bike(self, location):

        # not busy, reachable, with battery
        # TODO [OPTIONAL] if not busy and low battery => send to charge

        # import time
        # start = time.time()
        # filter by not busy and with battery
        available_bikes = [bike for bike in self.bikes if not bike.busy and bike.battery.level > self.BATTERY_MIN_LEVEL]
        # print("filter available", time.time()-start)
        bikes_lon = [bike.location.lon for bike in available_bikes]
        bikes_lat = [bike.location.lat for bike in available_bikes]
        locations = np.array((bikes_lon, bikes_lat)).transpose()
        # print("get available locations", time.time()-start)

        # start = time.time()
        # create kd-tree and find k nearest
        kdtree = spatial.KDTree(locations, leafsize=50)  # , compact_nodes=False, balanced_tree=False)
        # print("create kd-tree", time.time()-start)
        k = min(10, len(available_bikes))
        d, bikes_id = kdtree.query(location.get_loc(), k)
        # print("query kd-tree", time.time()-start)

        # start = time.time()
        # get nodes in graph and estimate shortest path lengths
        user_node = location.node
        bikes_nodes = [available_bikes[i].location.node for i in bikes_id]
        # print("get nodes", time.time()-start)
        distances = self.graph.network.shortest_path_lengths(np.tile(user_node, k), bikes_nodes)
        bikes_id, distances = sort_lists(bikes_id, distances, 1)
        # print("shortest path", time.time()-start)

        # look for walkable ones
        for bid, dist in zip(bikes_id, distances):
            bike = available_bikes[bid]
            reachable = dist < self.AUTONOMOUS_RADIUS
            if reachable:
                bike.busy = True
                return bike.id, bike.location

        logging.info("[%.2f] No bikes in reachable distance" % (self.env.now))
        return None, None

    def bike_ride(self, bike_id, location):
        bike = self.bikes[bike_id]
        yield self.env.process(bike.ride(location))

    def autonomous_drive(self, bike_id, location):
        bike = self.bikes[bike_id]
        yield self.env.process(bike.autonomous_drive(location))

    def station_has_bikes(self, station_id):
        station = self.stations[station_id]
        return station.has_bikes()

    def station_has_docks(self, station_id):
        station = self.stations[station_id]
        return station.has_docks()

    def station_choose_bike(self, station_id):
        station = self.stations[station_id]
        return station.choose_bike()

    def station_attach_bike(self, station_id, bike_id):
        station = self.stations[station_id]
        station.attach_bike(bike_id)

    def station_detach_bike(self, station_id, bike_id):
        station = self.stations[station_id]
        station.detach_bike(bike_id)

    def bike_register_unlock(self, bike_id, user_id):
        bike = self.bikes[bike_id]
        bike.register_unlock(user_id)

    def bike_register_lock(self, bike_id, user_id):
        bike = self.bikes[bike_id]
        bike.register_lock(user_id)

    def bike_busy(self, bike_id):
        bike = self.bikes[bike_id]
        return bike.busy

    def bike_unlock(self, bike_id, user_id):
        bike = self.bikes[bike_id]
        bike.unlock(user_id)

    def bike_lock(self, bike_id):
        bike = self.bikes[bike_id]
        bike.lock()

    def bike_charge(self, bike_id):
        bike = self.bikes[bike_id]
        low_battery = bike.battery.level < self.BATTERY_MIN_LEVEL
        if low_battery:
            yield self.env.process(bike.autonomous_charge())
