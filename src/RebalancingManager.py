import os
import logging
from numpy.lib.function_base import select

import pandas as pd
import numpy as np
from scipy.optimize import linprog
from .Location import Location


class RebalancingManager:
    # makes recharging decisions
    def __init__(self, env, config, graph, ui):
        self.env = env
        self.config = config
        self.graph = graph
        self.ui = ui

        self.update_every = 15 # [min]
        self.predict_ahead = 15 # [min]
        self.predict_window = 45 # [min]  

        self.update_every = config["REBALANCING_EVERY"] # [min]
        self.predict_ahead = config["REBALANCING_AHEAD"] # [min]
        self.predict_window = config["REBALANCING_WINDOW"] # [min]
        self.battery_min_level = config["BATTERY_MIN_LEVEL"] # [%]

        print("Loading Rebalancing")

        path = os.path.join("data", "demand_grid.csv")
        self.demand = pd.read_csv(path, index_col=0)

        self.grid = self.demand.copy()
        self.grid = self.demand.drop_duplicates(["group_lon", "group_lat"]).reset_index()
        self.grid = self.grid.drop(columns=["ts", "unix", "lon", "lat"])
        self.n = len(self.grid)
        

        # self.demand = self.demand.reset_index()
        # self.demand.set_index(["group_lon", "group_lat"], drop=False)

        self.idx = pd.MultiIndex.from_arrays([self.grid.group_lon, self.grid.group_lat])
        

        self.routing = Routing(self.grid, self.graph)

        print("Done Rebalancing")


    def set_bikes(self, bikes):
        self.bikes = bikes

    def start(self):
        self.env.process(self.predictive_demand())

    def predictive_demand(self):
        print("Rebalancing ongoing")
        while True:
            logging.info("[%.2f] Demand check" % (self.env.now))

            window_start = self.env.now + self.predict_ahead * 60
            window_stop  = window_start + self.predict_window * 60


            # data = pd.DataFrame({
            #     "demand": np.zeros(self.n),
            #     "bikes": np.zeros(self.n)
            # }, index = self.idx)
            bikes_vector = np.zeros(self.n, dtype=np.int)

            subset = self.demand.loc[window_start:window_stop]
            subset = pd.concat([subset, self.grid], axis=0, join="outer", ignore_index=True, sort=False)
            demand_vector = subset.groupby(["group_lon", "group_lat"]).size().values - 1
            # subset = subset.set_index(["group_lon", "group_lat"])
            # subset = subset.merge(data, how="right", left_index=True, right_index=True)
            # demand_vector = subset.groupby(level=[0,1]).size().values-1  

            # self.bikes_location = np.array([[bike.location.lon, bike.location.lat, bike.location.node] for bike in self.bikes])



            bikes_id = []
            bikes_cell = []
            for bike in self.bikes:
                if not bike.busy and bike.battery.level > self.battery_min_level:
                    lon = bike.location.lon
                    lat = bike.location.lat
                    cond = (lon > self.grid.lon_lb.values) & (lon < self.grid.lon_ub.values) & (lat > self.grid.lat_lb.values) & (lat < self.grid.lat_ub.values)
                    row = self.grid.index[cond].tolist()

                    if len(row) > 0:
                        # bike.grid_id = row[0]
                        
                        bikes_id.append(bike.id)
                        bikes_cell.append(row[0])

                        bikes_vector[row[0]] += 1
            
            bikes_id = np.array(bikes_id)
            bikes_cell = np.array(bikes_cell)
            
            



            s = self.routing.optimize(demand_vector, bikes_vector)
            
            cell_from_id, cell_to_id = np.where(s > 0)
            num_bikes = s[s > 0]
            num_rebalances = len(num_bikes)
            # print(self.env.now, "numbikes rebalancing", num_bikes, np.sum(num_bikes))
            
            # logging.info(
            #     "[%.2f] Rebalancing info: " % (self.env.now) + "\n" +
            #     "demand_vector: " + str(demand_vector) + "\n" +
            #     "bikes_vector: " + str(bikes_vector) + "\n" +
            #     "Bikes ID: " + str(bikes_id) + "\n" +
            #     "Bikes Cell: " + str(bikes_cell) + "\n" +
            #     "Cell from: " + str(cell_from_id) + "\n" +
            #     "Cell to: " + str(cell_to_id) + "\n" +
            #     "Num bikes: " + str(num_bikes) + "\n" +
            #     "Num rebalances: " + str(num_rebalances) 
            # )

            chosen = -np.ones_like(bikes_id, dtype=int)
            for i in range(num_rebalances):
                
                allowed = bikes_id[chosen == -1][bikes_cell[chosen == -1] == cell_from_id[i]]
                if len(allowed) > num_bikes[i]:
                    selected = np.random.choice(allowed, num_bikes[i], replace=False)
                else:
                    selected = allowed
                for j in selected:
                    chosen[bikes_id == j] = i

            for i in range(len(bikes_id)):
                if chosen[i] != -1:
                    bike_id = bikes_id[i]
                    cell_to = self.grid.iloc[cell_to_id[chosen[i]]]

                    lon = np.random.uniform(cell_to.lon_lb, cell_to.lon_ub)
                    lat = np.random.uniform(cell_to.lat_lb, cell_to.lat_ub)
                    # lon = (cell_to.lon_lb + cell_to.lon_ub)/2
                    # lat = (cell_to.lat_lb + cell_to.lat_ub)/2
                    node = self.graph.network.get_node_ids([lon], [lat])[0]
                    destination = Location(lon, lat, node)    
                
                    if not self.bikes[bike_id].busy:
                        logging.info("[%.2f] Rebalancing bike %d" % (self.env.now, bike_id))
                        self.env.process(self.ui.autonomous_drive(bike_id, destination, user_id=-1, magic=False, rebalancing=True, liberate=True, charge=True))
                        

            # WITH ROUTING OPTIMIZATION
            # for i in range(num_rebalances):
            #     selected = []
            #     allowed_bikes = bikes_id[bikes_cell == cell_from_id[i]]
            #     allowed_bikes = np.unique(allowed_bikes)
            #     # WITHOUT ROUTING OPTIMIZATION
            #     # allowed_bikes = bikes_id
            #     if len(allowed_bikes) > num_bikes[i]:
            #         selected = np.random.choice(allowed_bikes, num_bikes[i], replace=False)
            #     else:
            #         selected = allowed_bikes
            #     for j in selected:
            #         cell_to = self.grid.iloc[cell_to_id[i]]

            #         lon = np.random.uniform(cell_to.lon_lb, cell_to.lon_ub)
            #         lat = np.random.uniform(cell_to.lat_lb, cell_to.lat_ub)
            #         lon = (cell_to.lon_lb + cell_to.lon_ub)/2
            #         lat = (cell_to.lat_lb + cell_to.lat_ub)/2
            #         node = self.graph.network.get_node_ids([lon], [lat])[0]
            #         destination = Location(lon, lat, node)    
                    
            #         if not self.bikes[j].busy:
            #             logging.info("[%.2f] Rebalancing bike %d" % (self.env.now, j))
            #             self.env.process(self.ui.autonomous_drive(j, destination, user_id=-1, magic=False, rebalancing=True, liberate=True))
            #             self.env.process(self.ui.bike_charge(j))
                    
            yield self.env.timeout(self.update_every * 60)  # check every update_every mins




class Routing:

    def __init__(self, grid, graph):
        
        self.grid = grid
        self.graph = graph

        self.n = len(grid)

        print("Loading Routing")

        self.grid["lon"] = (self.grid.lon_lb + self.grid.lon_ub)/2
        self.grid["lat"] = (self.grid.lat_lb + self.grid.lat_ub)/2
        self.grid["node"] = self.graph.network.get_node_ids(self.grid.lon, self.grid.lat)
        self.grid["location"] = None
        self.grid["location"] = self.grid.apply(lambda x: Location(x.lon, x.lat, x.node), axis=1)
        # for i in range(len(self.grid)):
        #     self.grid["location"][i] = Location(self.grid.lon[i], self.grid.lat[i], self.grid.node[i])

        self.dist = self.compute_distances()
        self.slack = np.ones(self.n)*1e6
        self.cost = np.concatenate([self.dist.flatten(), self.slack])

        self.A = self.get_A()

        print("Done Routing")


    def get_A(self):
        n = self.n
        A = np.zeros((2*n, n**2 + n))

        for i in range(n):
            for j in range(n):
                A[i, i*n + j] = 1

                A[n+i, j*n + i] = -1

            A[n+i, n**2 + i] = -1
        return A

    def get_b(self, bikes, demand):
        n = self.n
        b = np.zeros((2*n))
        for i in range(n):
            b[i] =  bikes[i]
            b[n+i] =  -demand[i]
        return b


    def compute_distances(self):
        n = self.n
        dist = np.empty((n, n))
        for i in range(n):
            for j in range(n):
                if i == j:
                    dist[i,j] = 0
                else:
                    a = self.grid.location[i]
                    b = self.grid.location[j]
                    # dist[i,j] = np.sqrt((a.lon-b.lon)**2 + (a.lat-b.lat)**2)
                    dist[i,j] = self.graph.shortest_path_length(a, b)/1000
        return dist

    def optimize(self, demand, bikes):
        n = self.n
        cost = self.cost
        A = self.A
        b = self.get_b(bikes, demand)
        res = linprog(c=cost, A_ub = A, b_ub = b, method='highs')
        s = np.round(res.x[:n**2]).reshape((self.n, self.n))
        np.fill_diagonal(s, 0)

        # print(np.sum(demand), np.sum(bikes), np.sum(s[s>0]))
        # s[s>0]
        # np.where(s>0)
        return s.astype(int)