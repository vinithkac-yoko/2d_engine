from dataclasses import dataclass, field


@dataclass
class Measurement:
    name: str
    value: float
    full_name: str = ""
    description: str = ""


@dataclass
class MeasurementSet:
    version: str = "0.5.1"
    units: str = "cm"
    full_name: str = ""
    gender: str = "female"
    pm_system: str = ""
    measurements: dict[str, Measurement] = field(default_factory=dict)

    def get(self, name: str, default: float = 0.0) -> float:
        m = self.measurements.get(name)
        return m.value if m else default

    def set(self, name: str, value: float) -> None:
        if name in self.measurements:
            self.measurements[name].value = value
        else:
            self.measurements[name] = Measurement(name=name, value=value)

    def to_dict(self) -> dict[str, float]:
        return {k: v.value for k, v in self.measurements.items()}
