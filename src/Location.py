import numpy as np


class Location:
    def __init__(self, lon=None, lat=None, node=None):
        self.lon = lon
        self.lat = lat
        self.node = node

    def get_loc(self):
        return [self.lon, self.lat]

    def get_node(self):
        return self.node

    def noise(self, r):
        radius_earth = 6371000.0
        radius = np.random.uniform(0, r)
        theta = np.random.uniform(0, 2 * np.pi)
        dx = radius * np.cos(theta)
        dy = radius * np.sin(theta)
        new_lon = self.lon + (dx / radius_earth) * (180 / np.pi) / np.cos(self.lat * np.pi / 180)
        new_lat = self.lat + (dy / radius_earth) * (180 / np.pi)
        self.lon = new_lon
        self.lat = new_lat
