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


class HumiditySensor(BaseSensor):
    def __init__(self):
        super().__init__(
            sensor_id="HUMIDITY_01",
            topic=TOPICS["sensors"]["humidity"],
            interval=SENSOR_INTERVALS["humidity"],
        )
        self.min_val, self.max_val = SENSOR_RANGES["humidity"]

    def read_value(self):
        return round(random.uniform(self.min_val, self.max_val), 1)

    def get_unit(self):
        return "%"


if __name__ == "__main__":
    sensor = HumiditySensor()
    sensor.start()
