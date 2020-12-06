
class Location:
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat

    def get(self):
        return [self.lon, self.lat]