import logging


class Battery:
    id_count = -1

    def __init__(self, capacity, charge_rate, discharge_rate):
        self.next_id()
        self.id = Battery.id_count

        self.capacity = capacity  # total energy
        self.charge_rate = charge_rate  # energy per time
        self.discharge_rate = discharge_rate  # energy per distance
        self.level = capacity

    def next_id(self):
        Battery.id_count += 1

    def charge(self, duration):
        self.level = min(self.capacity, self.level + self.charge_rate * duration)

    def discharge(self, distance):
        self.level = max(0, self.level - self.discharge_rate * distance)

    def total_charge_time(self):
        return (self.capacity - self.level) / self.charge_rate

    # def discharge(self, duration):
    #     self.level = max(0, self.level - self.discharge_rate * duration)
