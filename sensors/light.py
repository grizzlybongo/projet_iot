import random
import os
import importlib.util

try:
    from .base_sensor import BaseSensor
    from ..config import TOPICS, SENSOR_INTERVALS, SENSOR_RANGES
except Exception:
    project_root = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(project_root, "config.py")
    spec = importlib.util.spec_from_file_location("local_config", config_path)
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    TOPICS = cfg.TOPICS
    SENSOR_INTERVALS = cfg.SENSOR_INTERVALS
    SENSOR_RANGES = cfg.SENSOR_RANGES

    base_path = os.path.join(os.path.dirname(__file__), "base_sensor.py")
    spec2 = importlib.util.spec_from_file_location("base_sensor", base_path)
    bs = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(bs)
    BaseSensor = bs.BaseSensor


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
        return random.randint(int(self.min_val), int(self.max_val))

    def get_unit(self):
        return "lux"


if __name__ == "__main__":
    sensor = LightSensor()
    sensor.start()
