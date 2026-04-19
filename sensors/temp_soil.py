import random
import os
import importlib.util

try:
    # Preferred: package-relative imports when used as a package (python -m sensors.temp_soil)
    from .base_sensor import BaseSensor
    from ..config import TOPICS, SENSOR_INTERVALS, SENSOR_RANGES
except Exception:
    # Fallback for direct execution or environment where package name is shadowed
    project_root = os.path.dirname(os.path.dirname(__file__))
    # load config.py by path
    config_path = os.path.join(project_root, "config.py")
    spec = importlib.util.spec_from_file_location("local_config", config_path)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    TOPICS = cfg.TOPICS
    SENSOR_INTERVALS = cfg.SENSOR_INTERVALS
    SENSOR_RANGES = cfg.SENSOR_RANGES

    # load BaseSensor from sensors/base_sensor.py by path
    base_path = os.path.join(os.path.dirname(__file__), "base_sensor.py")
    spec2 = importlib.util.spec_from_file_location("base_sensor", base_path)
    bs = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(bs)
    BaseSensor = bs.BaseSensor


class TemperatureSoilSensor(BaseSensor):
    def __init__(self):
        super().__init__(
            sensor_id="TEMP_SOIL_01",
            topic=TOPICS["sensors"]["temp_soil"],
            interval=SENSOR_INTERVALS["temp_soil"],
        )
        self.min_temp, self.max_temp = SENSOR_RANGES["temp_soil"]

    def read_value(self):
        return round(random.uniform(self.min_temp, self.max_temp), 1)

    def get_unit(self):
        return "°C"


if __name__ == "__main__":
    sensor = TemperatureSoilSensor()
    sensor.start()
