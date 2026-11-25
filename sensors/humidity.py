from config import TOPICS, SENSOR_INTERVALS, SENSOR_RANGES, SENSOR_STEPS
from sensors.base_sensor import BaseSensor


class HumiditySensor(BaseSensor):
    def __init__(self):
        super().__init__(
            sensor_id="HUMIDITY_01",
            topic=TOPICS["sensors"]["humidity"],
            interval=SENSOR_INTERVALS["humidity"],
        )
        self.min_val, self.max_val = SENSOR_RANGES["humidity"]

    def read_value(self):
        return self._next_value(self.min_val, self.max_val, SENSOR_STEPS["humidity"], 1)

    def get_unit(self):
        return "%"


if __name__ == "__main__":
    sensor = HumiditySensor()
    sensor.start()
