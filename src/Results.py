import os
import datetime
import json
import logging
from .UserTrip import UserTrip
from .BikeTrip import BikeTrip


class Results:
    def __init__(self, config):
        self.user_trips_name = "user_trips.csv"
        self.bike_trips_name = "bike_trips.csv"
        self.config_name = "config.json"
        self.log_name = "app.log"

        self.mkpath()
        self.mkdir()

        self.setup_log()
        self.save_config(config)
        self.open_user_trips()
        self.open_bike_trips()

    def mkpath(self):
        cwd = os.getcwd()
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.path = os.path.join(cwd, "results", now)

    def mkdir(self):
        os.mkdir(self.path)

    def setup_log(self):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(
            filename=os.path.join(self.path, self.log_name), filemode="w", format="%(message)s", level=logging.INFO,
        )

    def open_user_trips(self):
        self.user_trips = open(os.path.join(self.path, self.user_trips_name), "a")
        self.user_trips.write(UserTrip.get_header())

    def add_user_trip(self, user_trip):
        self.user_trips.write(user_trip.get_data())

    def close_user_trips(self):
        self.user_trips.close()

    def open_bike_trips(self):
        self.bike_trips = open(os.path.join(self.path, self.bike_trips_name), "a")
        self.bike_trips.write(BikeTrip.get_header())

    def add_bike_trip(self, bike_trip):
        self.bike_trips.write(bike_trip.get_data())

    def close_bike_trips(self):
        self.bike_trips.close()

    def save_config(self, config):
        with open(os.path.join(self.path, self.config_name), "w") as f:
            json.dump(config, f)

    def close(self):
        self.close_user_trips()
        self.close_bike_trips()
