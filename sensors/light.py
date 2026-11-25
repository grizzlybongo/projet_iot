from config import TOPICS, SENSOR_INTERVALS, SENSOR_RANGES, SENSOR_STEPS
from sensors.base_sensor import BaseSensor


class LightSensor(BaseSensor):
    def __init__(self):
        super().__init__(
            sensor_id="LIGHT_01",
            topic=TOPICS["sensors"]["light"],
            interval=SENSOR_INTERVALS["light"],
        )
        self.min_val, self.max_val = SENSOR_RANGES["light"]

    def read_value(self):
        # light is typically an integer lux value
        return int(self._next_value(self.min_val, self.max_val, SENSOR_STEPS["light"], 0))

    def get_unit(self):
        return "lux"


if __name__ == "__main__":
    sensor = LightSensor()
    sensor.start()
