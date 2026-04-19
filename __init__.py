"""greenhouse package initializer

This file makes the project root importable as the 'greenhouse' package
so package-relative imports like `from ..config import ...` work when modules
are executed as `python -m greenhouse.actuators.base_actuator` from the
parent directory.

Keep this file minimal; treat it as a marker for the package.
"""

__all__ = ["config", "sensors", "actuators"]
