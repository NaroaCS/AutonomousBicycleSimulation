import networkx as nx
import pandana as pdna
import numpy as np
from scipy import spatial
import pandas as pd
from .Location import Location
import pickle
import os

class Graph:
    def __init__(self, name=None):
        self.path = os.path.join("data", "graph")
        if name is None:
            name = "greater_boston_road"
        self.name = name
        self.start()
        pass

    def start(self):
        print("Loading graph")
        if not hasattr(self, "G"):
            self.load_graphml()
            self.process_graph()
            self.compute_nodes_edges()
            self.create_kdtree_nodes()
            self.create_network()

    def save(self):
        file_h5 = os.path.join(self.path, self.name + ".h5")
        self.network.save_hdf5(file_h5)
        network = self.network

        # network cannot be serialized with pickle (cython error)
        self.network = None
        file_pkl = os.path.join(self.path, self.name + ".pkl")
        with open(file_pkl, "wb") as f:
            pickle.dump(self, f)
        self.network = network

    @staticmethod
    def load(name):
        path = os.path.join("data", "graph")
        file_pkl = os.path.join(path, name + ".pkl")
        with open(file_pkl, "rb") as f:
            graph = pickle.load(f)
        file_h5 = os.path.join(path, name + ".h5")
        graph.network = pdna.Network.from_hdf5(file_h5)
        return graph

    def load_graphml(self):
        # path = "./data/greater_boston_road.graphml"
        # path = "./data/greater_boston_walk.graphml"
        file_graphml = os.path.join(self.path, self.name + ".graphml")
        self.G = nx.read_graphml(file_graphml)

    def process_graph(self):
        # UNDIRECTED
        self.G = self.G.to_undirected()

        # REMOVE DISCONNECTED
        S = [self.G.subgraph(c).copy() for c in sorted(nx.connected_components(self.G), key=len, reverse=True)]
        # print([len(x) for x in S])
        self.G = nx.relabel.convert_node_labels_to_integers(S[0])

    def compute_nodes_edges(self):
        # NODES AND EDGES
        nodes_x = [float(x) for x in nx.get_node_attributes(self.G, "x").values()]
        nodes_y = [float(y) for y in nx.get_node_attributes(self.G, "y").values()]
        self.nodes = np.column_stack([nodes_x, nodes_y])
        self.edges = [float(x) for x in nx.get_edge_attributes(self.G, "length").values()]

    def create_kdtree_nodes(self):
        self.kdtree_nodes = spatial.cKDTree(self.nodes, leafsize=30)

    def closest_node_kdtree(self, location, k=1):
        if not self.kdtree_nodes:
            self.create_kdtree_nodes()
        distance, closest = self.kdtree_nodes.query(location.get_loc(), k)
        return closest

    def create_kdtree_stations(self, stations):
        self.kdtree_stations = spatial.KDTree(stations)

    def precompute_stations_nodes(self, locations):
        pts = pd.DataFrame(locations, columns=["lon", "lat"])
        self.stations_nodes = self.network.get_node_ids(pts.lon, pts.lat)
        return self.stations_nodes

    def precompute_nearest_stations(self, locations, maxdist, maxitems):
        self.maxitems = maxitems
        pts = pd.DataFrame(locations, columns=["lon", "lat"])
        self.network.set_pois(
            category="stations", maxdist=maxdist, maxitems=maxitems, x_col=pts.lon, y_col=pts.lat,
        )

        self.nearest_stations = self.network.nearest_pois(distance=maxdist, category="stations", num_pois=maxitems, include_poi_ids=True,)

        # TODO: preprocess data to fast query

    def closest_station_kdtree(self, location, k=1):
        if not self.kdtree_stations:
            self.create_kdtree_stations()
        distance, closest = self.kdtree_stations.query(location.get_loc(), k)
        return closest

    def create_network(self):
        nodes_df = pd.DataFrame(self.nodes, columns=["x", "y"])
        edges_df = nx.to_pandas_edgelist(self.G)

        self.network = pdna.Network(nodes_df["x"], nodes_df["y"], edges_df["source"], edges_df["target"], edges_df[["length"]],)
        # self.network.precompute(500)

    def route(self, from_lon, from_lat, to_lon, to_lat):
        from_location = Location(from_lon, from_lat)  # TODO: remove
        to_location = Location(to_lon, to_lat)  # TODO: remove
        return self.shortest_path(from_location, to_location)

    def closest_nodes(self, locations):
        lon = [loc.lon for loc in locations]
        lat = [loc.lat for loc in locations]
        return self.network.get_node_ids(lon, lat)

        coords = [loc.get_loc() for loc in locations]
        pts = pd.DataFrame(coords, columns=["lon", "lat"])
        return self.network.get_node_ids(pts.lon, pts.lat)

    def shortest_path(self, from_location, to_location):
        from_closest, to_closest = self.closest_nodes([from_location, to_location])
        return self.network.shortest_path(from_closest, to_closest)

    def shortest_path_length(self, from_location, to_location):
        # from_closest, to_closest = self.closest_nodes([from_location, to_location])
        return self.network.shortest_path_length(from_location.node, to_location.node)

    # TODO: remove? review
    def shortest_paths_multiple(self, from_locations, to_locations):
        n_from, n_to = len(from_locations), len(to_locations)
        closests = self.closest_nodes([from_locations, to_locations])

        origs = [o for o in closests for d in closests]
        dests = [d for o in closests for d in closests]
        return self.network.shortest_path_lengths(np.tile(closests[:n_from], n_to), closests[n_from:])

    # TODO: remove? review
    def shortest_path_length_stations(self, from_location):
        # OPTION A: return air-distance to k stations via kdtree
        # distances, closests = self.kdtree_stations.query(from_location.get_loc(), 10)
        # return closests, distances

        # OPTION B: use precomputed poi and precomputed closest nodes

        user_node = from_location.node  # self.closest_nodes([from_location])
        k = min(10, self.maxitems)
        k = self.maxitems

        distances = self.nearest_stations.values[user_node, :k]
        stations_id = self.nearest_stations.values[user_node, self.maxitems : self.maxitems + k]

        distances = distances[~np.isnan(stations_id)].tolist()
        stations_id = stations_id[~np.isnan(stations_id)].astype(int).tolist()

        user_location = np.radians(np.array(from_location.get_loc()))
        stations_location = np.radians(self.kdtree_stations.data[stations_id])
        air_distances = Graph.equirect(user_location[0], user_location[1], stations_location[:, 0], stations_location[:, 1],)
        return stations_id, distances, air_distances

        # OPTION C: filter k air-nearest stations via kdtree + shortest-path via graph
        k = 10
        stations_id = self.closest_station_kdtree(from_location, k)
        user_node = from_location.node  # self.closest_nodes([from_location])
        distances = self.network.shortest_path_lengths(np.tile(user_node, k), self.stations_nodes[stations_id])
        # print(stations_id, self.stations_nodes[stations_id], user_node, distances)
        stations_id, distances = Graph.sort_lists(stations_id, distances, 1)
        return stations_id, distances

    @staticmethod
    def sort_lists(x, y, key=0):
        tuples = zip(*sorted(zip(x, y), reverse=False, key=lambda v: v[key]))
        x, y = [list(tuple) for tuple in tuples]
        return x, y

    @staticmethod
    def equirect(lonA, latA, lonB, latB):
        R = 6378137.0
        x = (lonB - lonA) * np.cos(0.5 * (latB + latA))
        y = latB - latA
        d = R * np.sqrt(x * x + y * y)
        return d


def main():
    graph = Graph()
    from_lon = -71.058099
    from_lat = 42.361942
    to_lon = -71.087446
    to_lat = 42.360590
    route = graph.route(from_lon, from_lat, to_lon, to_lat)
    print(route)


if __name__ == "__main__":
    main()
