import logging


class EnergyManager:
    # makes recharging decisions
    def __init__(self, env, config):
        self.env = env
        self.config = config

        self.BATTERY_MIN_LEVEL = config["BATTERY_MIN_LEVEL"]

    def set_bikes(self, bikes):
        self.bikes = bikes

    def start(self):
        self.env.process(self.battery_check())

    def battery_check(self):
        while True:
            logging.info("[%.2f] Battery check" % (self.env.now))
            for bike in self.bikes:
                low_battery = bike.battery.level < self.BATTERY_MIN_LEVEL
                busy = bike.busy
                if not busy and low_battery:  # Otherwise it could be already on the way to charging
                    self.env.process(bike.autonomous_charge())
            yield self.env.timeout(10 * 60)  # check every 10 mins
