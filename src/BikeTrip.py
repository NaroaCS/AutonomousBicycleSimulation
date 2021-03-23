class BikeTrip:
    id_count = -1
    header = [
        # "trip_id",
        "bike_id",
        "user_id",
        "mode",
        "trip_type",
        "time_departure",
        "time_ride",
        "time_charge",
        "magic_bike",
        "magic_dock",
        "origin_station",
        "destination_station",
        "origin_lon",
        "origin_lat",
        "destination_lon",
        "destination_lat",
        "battery_in",
        "battery_out",
    ]

    def __init__(self):
        self.next_id()
        self.id = BikeTrip.id_count

        self.store = dict.fromkeys(BikeTrip.header, "")
        # self.set("trip_id", self.id)

    @classmethod
    def reset(cls):
        BikeTrip.id_count = -1

    def next_id(self):
        BikeTrip.id_count += 1

    @staticmethod
    def get_header():
        return ",".join(BikeTrip.header) + "\n"

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
