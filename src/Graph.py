
import networkx as nx
import pandana as pdna
import os
import numpy as np
from scipy import spatial
import pandas as pd
from .Location import Location

class Graph:
    def __init__(self):
        self.start()

    def start(self):
        print('Loading graph')
        if not hasattr(self, 'G'):
            self.load_graphml()
            self.process_graph()
            self.get_nodes_edges()
            self.create_kdtree()
            self.create_network()
        print('Loaded graph')
        

    def load_graphml(self):
        path = './data/greater_boston_road.graphml'
        self.G = nx.read_graphml(path)

    def process_graph(self):
        # UNDIRECTED
        self.G = self.G.to_undirected()

        # REMOVE DISCONNECTED
        S = [self.G.subgraph(c).copy() for c in sorted(nx.connected_components(self.G), key=len, reverse=True)]
        [len(x) for x in S]
        self.G = nx.relabel.convert_node_labels_to_integers(S[0])

    def get_nodes_edges(self):
        # NODES AND EDGES
        nodes_x = [float(x) for x in nx.get_node_attributes(self.G, 'x').values()]
        nodes_y = [float(y) for y in nx.get_node_attributes(self.G, 'y').values()]
        self.nodes = np.column_stack([nodes_x, nodes_y])
        self.edges = [float(x) for x in nx.get_edge_attributes(self.G, 'length').values()]

    def create_kdtree(self):
        self.kdtree = spatial.KDTree(self.nodes)

    def get_closest_node_kdtree(self, location):
        if not self.kdtree_nodes:
            self.create_kdtree()
        distance, closest = self.kdtree_nodes.query(location.get(), 1)
        return closest

    def create_network(self):
        nodes_df = pd.DataFrame(self.nodes, columns=['x','y'])
        edges_df = nx.to_pandas_edgelist(self.G)

        self.network = pdna.Network(nodes_df['x'], nodes_df['y'], edges_df['source'], edges_df['target'], edges_df[['length']])
        # self.network.precompute(10000)

    def get_route(self, from_lon, from_lat, to_lon, to_lat):
        from_location = Location(from_lon, from_lat)
        to_location = Location(to_lon, to_lat)
        return self.get_shortest_path(from_location, to_location)

    def get_closest_nodes(self, locations):
        coords = np.array([loc.get() for loc in locations])
        pts = pd.DataFrame(coords, columns=['lon', 'lat'])
        return self.network.get_node_ids(pts.lon, pts.lat)

    def get_shortest_path(self, from_location, to_location):
        from_closest, to_closest = self.get_closest_nodes([from_location, to_location])
        return self.network.shortest_path(from_closest, to_closest)

    def get_shortest_path_length(self, from_location, to_location):
        from_closest, to_closest = self.get_closest_nodes([from_location, to_location])
        return self.network.shortest_path_length(from_closest, to_closest)
    
    def get_shortest_paths(self, from_locations, to_locations):
        n_from, n_to = len(from_locations), len(to_locations)
        closests = self.get_closest_nodes([from_locations, to_locations])

        origs = [o for o in closests for d in closests]
        dests = [d for o in closests for d in closests]
        return self.network.shortest_path_lengths(np.tile(closests[:n_from],n_to), closests[n_from:])

def main():
    graph = Graph()
    from_lon = -71.058099
    from_lat = 42.361942
    to_lon = -71.087446
    to_lat = 42.360590
    route = graph.get_route(from_lon, from_lat, to_lon, to_lat)
    print(route)

if __name__ == '__main__':
    main() 