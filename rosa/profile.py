# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Versioned, immutable operating requirements supplied by the integrator."""
from dataclasses import asdict, dataclass, fields
import math


@dataclass(frozen=True)
class OperationalProfile:
    """Per-robot policy. Defaults describe the included simulation scenario.

    Source names are allowlists, not cryptographic authentication. Integrators
    must authenticate the adapter and synchronize clocks before requiring
    acquisition timestamps from a remote sensor.
    """

    battery_ttl_s: float = 10.0
    obstacle_ttl_s: float = 3.0
    estop_ttl_s: float = 3.0
    position_ttl_s: float = 10.0
    minimum_battery: float = 20.0
    docking_battery: float = 8.0
    minimum_confidence: float = 0.8
    proposal_ttl_s: float = 30.0
    require_acquisition_time: bool = False
    allowed_sources: tuple[str, ...] = ()

    def __post_init__(self):
        for name in ("battery_ttl_s", "obstacle_ttl_s", "estop_ttl_s",
                     "position_ttl_s", "proposal_ttl_s"):
            self._number(name, 0, 86400, exclusive_min=True)
        for name in ("minimum_battery", "docking_battery"):
            self._number(name, 0, 100)
        self._number("minimum_confidence", 0, 1)
        if self.docking_battery > self.minimum_battery:
            raise ValueError("Docking threshold cannot exceed the operating threshold")
        if type(self.require_acquisition_time) is not bool:
            raise ValueError("require_acquisition_time must be a boolean")
        if (not isinstance(self.allowed_sources, tuple)
                or len(self.allowed_sources) > 100
                or any(not isinstance(s, str) or not 1 <= len(s) <= 120
                       for s in self.allowed_sources)
                or len(set(self.allowed_sources)) != len(self.allowed_sources)):
            raise ValueError("allowed_sources must contain unique source names")

    def _number(self, name, lower, upper, exclusive_min=False):
        value = getattr(self, name)
        if (type(value) not in (int, float) or not math.isfinite(value)
                or value < lower or value > upper or (exclusive_min and value == lower)):
            raise ValueError(f"Invalid operating requirement: {name}")

    @property
    def ttl(self):
        return {name: getattr(self, name + "_ttl_s")
                for name in ("battery", "obstacle", "estop", "position")}

    def to_dict(self):
        result = asdict(self)
        result["allowed_sources"] = list(self.allowed_sources)
        return result

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or set(value) - {f.name for f in fields(cls)}:
            raise ValueError("Unknown operating requirement")
        data = dict(value)
        if "allowed_sources" in data:
            if not isinstance(data["allowed_sources"], (list, tuple)):
                raise ValueError("allowed_sources must be a list")
            data["allowed_sources"] = tuple(data["allowed_sources"])
        return cls(**data)
