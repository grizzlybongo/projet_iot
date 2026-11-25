from config import TOPICS, SENSOR_INTERVALS, SENSOR_RANGES, SENSOR_STEPS
from sensors.base_sensor import BaseSensor


class TemperatureSoilSensor(BaseSensor):
    def __init__(self):
        super().__init__(
            sensor_id="TEMP_SOIL_01",
            topic=TOPICS["sensors"]["temp_soil"],
            interval=SENSOR_INTERVALS["temp_soil"],
        )
        self.min_temp, self.max_temp = SENSOR_RANGES["temp_soil"]

    def read_value(self):
        return self._next_value(self.min_temp, self.max_temp, SENSOR_STEPS["temp_soil"], 1)

    def get_unit(self):
        return "°C"


if __name__ == "__main__":
    sensor = TemperatureSoilSensor()
    sensor.start()
