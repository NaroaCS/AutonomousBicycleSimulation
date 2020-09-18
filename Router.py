#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 13:40:03 2020

@author: doorleyr
"""

import pandas as pd
import json
#from shapely.geometry import  shape
import math
import networkx as nx
from scipy import spatial
import numpy as np



def get_haversine_distance(point_1, point_2):
    """
    Calculate the distance between any 2 points on earth given as [lon, lat]
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [point_1[0], point_1[1], 
                                                point_2[0], point_2[1]])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371000 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

class Network():
    def __init__(self):
        try:
            print('Attempting to load saved network')
            self.nodes=json.load(open('network_nodes.json'))
            self.edges=pd.read_csv('network_edges.csv')
        except:
            print('Network not yet saved. Building network: takes a few minutes.')
            self.nodes, self.edges=self.build_network_for_bluebikes()
        self.G=self.network_dfs_to_nx()
        self.create_nodes_kdtree()
        
    def rename_nodes(self, nodes_df, edges_df, node_id_name, to_name, from_name):
        nodes_df['old_node_id']=nodes_df[node_id_name].copy()
        nodes_df['node_id']=range(len(nodes_df))
        node_name_map={nodes_df.iloc[i]['old_node_id']:i for i in range(len(nodes_df))}
        rev_node_name_map={v:str(k) for k,v in node_name_map.items()}
        edges_df['from_node_id']=edges_df.apply(lambda row: node_name_map[row[from_name]], axis=1)
        edges_df['to_node_id']=edges_df.apply(lambda row: node_name_map[row[to_name]], axis=1)
        return nodes_df, edges_df, rev_node_name_map
    
    def get_osm_network(self, bounds):
        import osmnet
        nodes_df,edges=osmnet.load.network_from_bbox(lat_min=bounds[1], lng_min=bounds[0], lat_max=bounds[3], 
                                  lng_max=bounds[2], bbox=None, network_type='drive', 
                                  two_way=True, timeout=180, 
                                  custom_osm_filter=None)
        nodes_df, edges, node_name_map =self.rename_nodes(nodes_df, edges, 'id', 'to', 'from')
        nodes_list=[[nodes_df.iloc[i]['x'], nodes_df.iloc[i]['y']] for i in range(len(nodes_df))]
        return nodes_list, edges
    
    def network_dfs_to_nx(self):  
        G=nx.Graph()
        for i, row in self.edges.iterrows():
            G.add_edge(row['from_node_id'], row['to_node_id'], 
                       weight=row['distance'])
        return G
    
    def create_nodes_kdtree(self):
        self.kdtree_nodes=spatial.KDTree(self.nodes)
    
    def get_closest_node(self, lon, lat):
        if not self.kdtree_nodes:
            self.create_nodes_kdtree()
        distance, closest=self.kdtree_nodes.query([lon, lat], 1)
        return closest
    
    def get_node_path(self, o_node, d_node):
        node_path=nx.dijkstra_path(self.G,o_node, d_node, 'weight')
        return node_path
    
    def get_path_coords(self, node_path):
        coord_path=[self.nodes[n] for n in node_path]
        return coord_path
                
    def get_path_distances(self, coord_path):
        distances=[get_haversine_distance(coord_path[i], coord_path[i+1]
            ) for i in range(len(coord_path)-1)]
        return distances
    
    def get_route(self, from_lon, from_lat, to_lon, to_lat):
        o_node=self.get_closest_node(from_lon, from_lat)
        d_node=self.get_closest_node(to_lon, to_lat)
        node_path=self.get_node_path(o_node, d_node)
        coord_path=self.get_path_coords(node_path)
        distances=self.get_path_distances(coord_path)
        cum_distances=[0] + list(np.cumsum(distances))
        return {'coords': coord_path, 'cum_distances': cum_distances}
        
    def build_network_for_bluebikes(self):   
        bb_data=pd.read_excel('201909-bluebikes-tripdata.xlsx')
        bounds=[min(bb_data['start station longitude']), #W
               min(bb_data['start station latitude']), #S
               max(bb_data['start station longitude']), #E
               max(bb_data['start station latitude'])] #N
        nodes, edges=self.get_osm_network(bounds)
        edges.to_csv('network_edges.csv')
        json.dump(nodes, open('network_nodes.json', 'w'))
        return nodes, edges
    
def main():
    network=Network()
    from_lon=-71.058099
    from_lat=42.361942
    to_lon= -71.087446
    to_lat=42.360590
    route=network.get_route(from_lon, from_lat, to_lon, to_lat)
    print(route)

if __name__ == '__main__':
    main() 
        

#
#all_routes={}
#for o in range(len(station_locations_df)):
#    o_id=station_locations_df.index[o]
#    print(o_id)
#    all_routes[o_id]={}
#    o_lon=station_locations_df.iloc[o]['start station longitude']
#    o_lat=station_locations_df.iloc[o]['start station latitude']
#    for d in range(len(station_locations_df)):
#        d_id=station_locations_df.index[d]
#        d_lon=station_locations_df.iloc[d]['start station longitude']
#        d_lat=station_locations_df.iloc[d]['start station latitude']
#        route=getOSRMDirections('bike', o_lon, o_lat, d_lon, d_lat)
#        all_routes[o_id][d_id]=route
#    json.dump(all_routes, './routes.json')
        