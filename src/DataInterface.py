import numpy as np
from scipy import spatial
import logging


class DataInterface:
    def __init__(self, env, graph, config):
        self.env = env
        self.graph = graph
        self.config = config

        self.stations = []
        self.bikes = []

        self.MODE = config["MODE"]
        self.WALK_RADIUS = config["WALK_RADIUS"]
        self.AUTONOMOUS_RADIUS = config["AUTONOMOUS_RADIUS"]
        self.BATTERY_MIN_LEVEL = config["BATTERY_MIN_LEVEL"]

        self.MAGIC_MIN_BIKES = config["MAGIC_MIN_BIKES"]
        self.MAGIC_MIN_DOCKS = config["MAGIC_MIN_DOCKS"]

    def set_bikes(self, bikes):
        self.bikes = bikes
        if self.MODE == 1 or self.MODE == 2:
            self.bikes_location = np.array([[bike.location.lon, bike.location.lat, bike.location.node] for bike in self.bikes])

    def set_stations(self, stations):
        self.stations = stations

    def set_data(self, stations, bikes):
        self.stations = stations
        self.bikes = bikes

    def dist(self, a, b):
        return self.graph.shortest_path_length(a, b)

    def select_start_station(self, location, visited_stations):
        (stations_id, road_distances, air_distances,) = self.graph.shortest_path_length_stations(location)

        # TODO: DONE remove visited from selection criteria
        # TODO: DONE calculate reason for magic bikes: return if there are walkable stations
        # TODO: DONE adapt walkable criteria to air-distance
        any_walkable = False
        for sid, dist in zip(stations_id, air_distances):
            station = self.stations[sid]
            has_bikes = station.has_bikes()
            walkable = dist < self.WALK_RADIUS
            if has_bikes and walkable:
                visited_stations.append(sid)
                return sid, station.location, visited_stations, True
            if walkable:
                any_walkable = True

        return None, None, visited_stations, any_walkable

    def select_end_station(self, destination, visited_stations):
        (stations_id, road_distances, air_distances,) = self.graph.shortest_path_length_stations(destination)

        for sid, dist in zip(stations_id, air_distances):
            station = self.stations[sid]
            has_docks = station.has_docks()
            walkable = dist < self.WALK_RADIUS
            if has_docks and walkable:
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] No docks in a walkable distance" % (self.env.now))
        return None, None, visited_stations

    def magic_bike(self, location, visited_stations):
        (stations_id, road_distances, air_distances,) = self.graph.shortest_path_length_stations(location)

        source_station_id = None
        for sid in stations_id:
            station = self.stations[sid]
            has_bikes = station.has_bikes(self.MAGIC_MIN_BIKES)
            if has_bikes:
                source_station_id = sid
                break

        if source_station_id is None:
            logging.info("[%.2f] No stations found as source of magic bike" % (self.env.now))
            return None, None, visited_stations, None, None

        for sid, dist in zip(stations_id, air_distances):
            station = self.stations[sid]
            has_docks = station.has_docks()
            walkable = dist < self.WALK_RADIUS
            if has_docks and walkable:
                bike_id = self.station_choose_bike(source_station_id)
                self.station_detach_bike(source_station_id, bike_id)
                self.station_attach_bike(sid, bike_id)
                if len(visited_stations) == 0 or visited_stations[-1] != sid:
                    visited_stations.append(sid)
                return (
                    sid,
                    station.location,
                    visited_stations,
                    bike_id,
                    source_station_id,
                )

        logging.info("[%.2f] No stations found as target for magic bike" % (self.env.now))
        return None, None, visited_stations, None, None

    def magic_dock(self, location, visited_stations):
        (stations_id, road_distances, air_distances,) = self.graph.shortest_path_length_stations(location)

        source_station_id = None
        for sid in stations_id:
            station = self.stations[sid]
            has_docks = station.has_docks(self.MAGIC_MIN_DOCKS)
            if has_docks:
                source_station_id = sid
                break

        if source_station_id is None:
            logging.info("[%.2f] No stations found as target of magic bike" % (self.env.now))
            return None, None, visited_stations, None, None

        for sid, dist in zip(stations_id, air_distances):
            station = self.stations[sid]
            has_bikes = station.has_bikes()
            walkable = dist < self.WALK_RADIUS
            if has_bikes and walkable:
                bike_id = self.station_choose_bike(sid)
                self.station_detach_bike(sid, bike_id)
                self.station_attach_bike(source_station_id, bike_id)
                if len(visited_stations) == 0 or visited_stations[-1] != sid:
                    visited_stations.append(sid)
                return (
                    sid,
                    station.location,
                    visited_stations,
                    bike_id,
                    source_station_id,
                )

        logging.info("[%.2f] No stations found as source for magic bike" % (self.env.now))
        return None, None, visited_stations, None, None

    def notwalkable_dock(self, destination, visited_stations):

        (stations_id, road_distances, air_distances,) = self.graph.shortest_path_length_stations(destination)

        for sid in stations_id:
            station = self.stations[sid]
            has_docks = station.has_docks()
            if has_docks:
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] ERROR: No station with docks -> Think about changing this part of the code" % (self.env.now))
        return None, None, visited_stations

    @staticmethod
    def cartesian(lon, lat):
        lat = lat * (np.pi / 180)
        lon = lon * (np.pi / 180)

        R = 6378137.0
        X = R * np.cos(lat) * np.cos(lon)
        Y = R * np.cos(lat) * np.sin(lon)
        Z = R * np.sin(lat)
        return np.array([X, Y, Z]).T

    @staticmethod
    def haversine_np(lon1, lat1, lon2, lat2):
        lon1 = np.radians(lon1)
        lat1 = np.radians(lat1)
        lon2 = np.radians(lon2)
        lat2 = np.radians(lat2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        R = 6378137.0
        return c * R

    @staticmethod
    def sort_lists(x, y, key=0):
        tuples = zip(*sorted(zip(x, y), reverse=False, key=lambda v: v[key]))
        x, y = [list(tuple) for tuple in tuples]
        return x, y

    def select_dockless_bike(self, location):
        # nearest, not busy and walkable

        # filter by not busy
        available_bikes = [bike for bike in self.bikes if not bike.busy]
        available_bikes_id = [bike.id for bike in available_bikes]
        locations = self.bikes_location[available_bikes_id]
        user_location = location.get_loc()

        # create kd-tree and find k nearest
        k = min(10, len(available_bikes_id))
        option = "degrees"  # "degrees", "cartesian", "balltree"
        if option == "degrees":
            kdtree = spatial.cKDTree(locations[:, :2], leafsize=50, compact_nodes=False, balanced_tree=False)
            _, bikes_id = kdtree.query(user_location, k)
            air_distances = DataInterface.haversine_np(user_location[0], user_location[1], locations[bikes_id, 0], locations[bikes_id, 1],)

        if option == "cartesian":
            locations_cartesian = DataInterface.cartesian(locations[:, 0], locations[:, 1])
            location_cartesian = DataInterface.cartesian(user_location[0], user_location[1])
            kdtree = spatial.cKDTree(locations_cartesian, leafsize=50, compact_nodes=False, balanced_tree=False,)
            air_distances, bikes_id = kdtree.query(location_cartesian, k)

        if option == "balltree":
            # alternative: use sklearn and haversine distance
            from sklearn.neighbors import BallTree

            R = 6371000
            bt = BallTree(np.deg2rad(locations[:, [1, 0]]), metric="haversine")
            loc = np.deg2rad(user_location)[::-1]
            air_distances, bikes_id = bt.query([loc], k)
            air_distances = air_distances[0]
            bikes_id = bikes_id[0]
            air_distances = air_distances * R

        # TODO: DONE check if nearest bike via-air is walkable => if not return None
        if air_distances[0] > self.WALK_RADIUS:
            logging.info("[%.2f] No bikes in walkable distance" % (self.env.now))
            return None, None

        # get nodes in graph and estimate shortest path lengths
        user_node = location.node
        bikes_nodes = locations[bikes_id, 2].astype(int)

        # TODO: if the walkable criteria is based on air-distances, do we need the road_distance?
        # only for sorting, because the bikes_id are selected based on kdtree (air-distances)
        distances = self.graph.network.shortest_path_lengths(np.tile(user_node, k), bikes_nodes)
        bikes_id, distances = DataInterface.sort_lists(bikes_id, distances, 1)
        air_distances, distances = DataInterface.sort_lists(air_distances, distances, 1)

        # look for walkable ones
        for bid, dist in zip(bikes_id, air_distances):
            bike = available_bikes[bid]
            walkable = dist < self.WALK_RADIUS
            if walkable:
                return bike.id, bike.location

        logging.info("[%.2f] No bikes in walkable distance" % (self.env.now))
        return None, None

    def select_dockless_bike_old(self, location):

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
        kdtree = spatial.cKDTree(locations, leafsize=50, compact_nodes=False, balanced_tree=False)
        # print("create kd-tree", time.time()-start)
        k = min(10, len(available_bikes))
        # k = min(10, locations.shape[0])
        air_distances, bikes_id = kdtree.query(location.get_loc(), k)
        # print("query kd-tree", time.time()-start)

        # TODO: DONE check if nearest bike via-air is walkable => if not return None
        if air_distances[0] > self.WALK_RADIUS:
            logging.info("[%.2f] No bikes in walkable distance" % (self.env.now))
            return None, None

        # start = time.time()
        # get nodes in graph and estimate shortest path lengths
        user_node = location.node
        bikes_nodes = [available_bikes[i].location.node for i in bikes_id]
        # print("get nodes", time.time()-start)

        # TODO: if the walkable criteria is based on air-distances, do we need the road_distance?
        # only for sorting, because the bikes_id are selected based on kdtree (air-distances)
        distances = self.graph.network.shortest_path_lengths(np.tile(user_node, k), bikes_nodes)
        bikes_id, distances = DataInterface.sort_lists(bikes_id, distances, 1)
        air_distances, distances = DataInterface.sort_lists(air_distances, distances, 1)
        # print("shortest path", time.time()-start)

        # look for walkable ones
        for bid, dist in zip(bikes_id, air_distances):
            bike = available_bikes[bid]
            walkable = dist < self.WALK_RADIUS
            if walkable:
                return bike.id, bike.location

        logging.info("[%.2f] No bikes in walkable distance" % (self.env.now))
        return None, None

    def select_charging_station(self, location, visited_stations):
        (stations_id, road_distances, air_distances,) = self.graph.shortest_path_length_stations(location)

        for sid in stations_id:
            station = self.stations[sid]
            has_docks = station.has_docks()
            if has_docks:
                visited_stations.append(sid)
                return sid, station.location, visited_stations

        logging.info("[%.2f] No charging stations with available space" % (self.env.now))
        return None, None, visited_stations

    def call_autonomous_bike(self, location):
        # not busy, reachable, with battery

        # filter by not busy and with battery
        available_bikes = [bike for bike in self.bikes if not bike.busy and bike.battery.level > self.BATTERY_MIN_LEVEL]
        available_bikes_id = [bike.id for bike in available_bikes]
        locations = self.bikes_location[available_bikes_id]
        user_location = location.get_loc()

        # create kd-tree and find k nearest
        k = min(10, len(available_bikes_id))
        option = "degrees"  # "degrees", "cartesian", "balltree"
        if option == "degrees":
            kdtree = spatial.cKDTree(locations[:, :2], leafsize=50, compact_nodes=False, balanced_tree=False)
            _, bikes_id = kdtree.query(user_location, k)
            air_distances = DataInterface.haversine_np(user_location[0], user_location[1], locations[bikes_id, 0], locations[bikes_id, 1],)

        if option == "cartesian":
            locations_cartesian = DataInterface.cartesian(locations[:, 0], locations[:, 1])
            location_cartesian = DataInterface.cartesian(user_location[0], user_location[1])
            kdtree = spatial.cKDTree(locations_cartesian, leafsize=50, compact_nodes=False, balanced_tree=False,)
            air_distances, bikes_id = kdtree.query(location_cartesian, k)

        if option == "balltree":
            # alternative: use sklearn and haversine distance
            from sklearn.neighbors import BallTree

            R = 6371000
            bt = BallTree(np.deg2rad(locations[:, [1, 0]]), metric="haversine")
            loc = np.deg2rad(user_location)[::-1]
            air_distances, bikes_id = bt.query([loc], k)
            air_distances = air_distances[0]
            bikes_id = bikes_id[0]
            air_distances = air_distances * R

        # TODO: DONE check if nearest bike via-air is walkable => if not return None
        if air_distances[0] > self.WALK_RADIUS:
            logging.info("[%.2f] No bikes in walkable distance" % (self.env.now))
            return None, None

        # get nodes in graph and estimate shortest path lengths
        user_node = location.node
        bikes_nodes = locations[bikes_id, 2].astype(int)

        # TODO: if the walkable criteria is based on air-distances, do we need the road_distance?
        # only for sorting, because the bikes_id are selected based on kdtree (air-distances)
        distances = self.graph.network.shortest_path_lengths(np.tile(user_node, k), bikes_nodes)
        bikes_id, distances = DataInterface.sort_lists(bikes_id, distances, 1)
        air_distances, distances = DataInterface.sort_lists(air_distances, distances, 1)

        # look for walkable ones
        for bid, dist in zip(bikes_id, distances):
            bike = available_bikes[bid]
            reachable = dist < self.AUTONOMOUS_RADIUS
            if reachable:
                bike.busy = True
                return bike.id, bike.location

        logging.info("[%.2f] No bikes in reachable distance" % (self.env.now))
        return None, None

    def call_autonomous_bike_old(self, location):

        # not busy, reachable, with battery

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
        kdtree = spatial.cKDTree(locations, leafsize=50, compact_nodes=False, balanced_tree=False)
        # print("create kd-tree", time.time()-start)
        k = min(10, len(available_bikes))
        air_distances, bikes_id = kdtree.query(location.get_loc(), k)
        # print("query kd-tree", time.time()-start)

        # TODO: DONE check if nearest bike via-air is walkable => if not return None
        if air_distances[0] > self.WALK_RADIUS:
            logging.info("[%.2f] No bikes in walkable distance" % (self.env.now))
            return None, None

        # start = time.time()
        # get nodes in graph and estimate shortest path lengths
        user_node = location.node
        bikes_nodes = [available_bikes[i].location.node for i in bikes_id]
        # print("get nodes", time.time()-start)

        # TODO: if the walkable criteria is based on air-distances, do we need the road_distance?
        # only for sorting, because the bikes_id are selected based on kdtree (air-distances)
        distances = self.graph.network.shortest_path_lengths(np.tile(user_node, k), bikes_nodes)
        bikes_id, distances = DataInterface.sort_lists(bikes_id, distances, 1)
        air_distances, distances = DataInterface.sort_lists(air_distances, distances, 1)
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

        if self.MODE == 1 or self.MODE == 2:
            self.bikes_location[bike_id] = [
                bike.location.lon,
                bike.location.lat,
                bike.location.node,
            ]

    def autonomous_drive(self, bike_id, location, user_id):
        bike = self.bikes[bike_id]
        yield self.env.process(bike.autonomous_drive(location, user_id))

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
