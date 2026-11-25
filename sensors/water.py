from config import TOPICS, SENSOR_INTERVALS, SENSOR_RANGES, SENSOR_STEPS
from sensors.base_sensor import BaseSensor


class WaterLevelSensor(BaseSensor):
    def __init__(self):
        super().__init__(
            sensor_id="WATER_01",
            topic=TOPICS["sensors"]["water"],
            interval=SENSOR_INTERVALS["water"],
        )
        self.min_val, self.max_val = SENSOR_RANGES["water"]

    def read_value(self):
        return self._next_value(self.min_val, self.max_val, SENSOR_STEPS["water"], 1)

    def get_unit(self):
        return "%"


if __name__ == "__main__":
    sensor = WaterLevelSensor()
    sensor.start()
