class UserTrip:
    id_count = -1
    header = [
        "user_id",
        "status",
        "bike_id",
        "mode",
        "time_departure",
        "time_target",
        "time_walk_origin",
        "time_ride",
        "time_wait",
        "time_walk_destination",
        "origin_lon",
        "origin_lat",
        "destination_lon",
        "destination_lat",
        "origin_visited_stations",
        "destination_visited_stations",
        "origin_station",
        "destination_station",
        "magic_bike",
        "magic_dock",
        "bike_lon",
        "bike_lat",
    ]

    def __init__(self):
        self.store = dict.fromkeys(UserTrip.header, "")

    @staticmethod
    def get_header():
        return ",".join(UserTrip.header) + "\n"

    def get_data(self):
        return ",".join(map(str, self.store.values())) + "\n"

    def set(self, key, value, digits=2):
        if key in self.store.keys():
            if isinstance(value, bool):
                value = int(value)
                value = str(value)
            elif isinstance(value, int):
                value = str(value)
            elif isinstance(value, float):
                if digits == 0:
                    value = int(value)
                else:
                    value = round(value, digits)
                value = str(value)
            self.store[key] = value
        else:
            raise BaseException
