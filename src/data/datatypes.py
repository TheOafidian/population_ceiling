from dataclasses import dataclass
from enum import Enum
from math import pi

class Role(Enum):

    FARMER = "farmer"
    NON_FARMER = "non-farmer"


@dataclass(frozen=True)
class Bucket:
    """A bucket represents 25 kgs of grain."""
    kilograms: float = 25.0
    pounds: float = 55.0


@dataclass
class Person:
    role: Role

    @property
    def annual_bucket_requirement(self) -> int:
        """
        Non farmers require 10 buckets per year.
        Farmers consume their own harvest and do not cound towards
        exported grain requirements
        """
        if self.role == Role.FARMER:
            return 0
        return 10

@dataclass
class Population:
    farmers: int = 0
    non_farmers: int = 0

    @property
    def annual_bucket_demand(self) -> int:
        """Buckets that must leave farms each year."""
        return self.non_farmers * 10

    @property
    def annual_grain_kg(self) -> float:
        return self.annual_bucket_demand * Bucket().kilograms

    @property
    def annual_grain_lbs(self) -> float:
        return self.annual_bucket_demand * Bucket().pounds


HECTARES_PER_SQ_MILE = 259

@dataclass(frozen=True)
class SupplyZone:
    """Base class for any food supply area."""
    square_miles: float

    @property
    def hectares(self) -> float:
        return self.square_miles * HECTARES_PER_SQ_MILE

@dataclass(frozen=True)
class LandSupplyZone(SupplyZone):
    """
    Farmland reachable by ox-cart.

    Default radius = 15 miles because a loaded ox-cart can travel
    roughly that distance in a working day.
    """
    radius_miles: float = 15.0

    def __init__(self, radius_miles: float = 15.0):
        area = pi * radius_miles**2
        super().__init__(square_miles=area)
        object.__setattr__(self, "radius_miles", radius_miles)


@dataclass(frozen=True)
class RiverSupplyCorridor(SupplyZone):
    """
    Navigable river corridor.

    Width is assumed to be 30 miles total
    (15 miles on each bank).
    """
    navigable_length_miles: float
    corridor_width_miles: float = 30.0

    def __init__(
        self,
        navigable_length_miles: float,
        corridor_width_miles: float = 30.0,
    ):
        area = navigable_length_miles * corridor_width_miles
        super().__init__(square_miles=area)
        object.__setattr__(self, "navigable_length_miles", navigable_length_miles)
        object.__setattr__(self, "corridor_width_miles", corridor_width_miles)



@dataclass(frozen=True)
class CoastalSupplyZone(SupplyZone):
    """
    Area supplied through coastal shipping.

    The worksheet treats this as effectively extending
    supply along the accessible coastline. Because the
    exact geometry varies, the area must be provided.
    """
    coastline_area_sq_miles: float

    def __init__(self, coastline_area_sq_miles: float):
        super().__init__(square_miles=coastline_area_sq_miles)
        object.__setattr__(self, "coastline_area_sq_miles", coastline_area_sq_miles)

@dataclass
class SoilType:
    name: str
    description: str
    plot_size: int
    yield_ratio: float
    arable: float

@dataclass
class RotationSystem:
    name: str
    modifier: float


@dataclass
class City:
    name: str
    land_zone: LandSupplyZone
    active_fisheries: bool = False
    salt_supply: bool = False
    river_corridor: RiverSupplyCorridor | None = None
    coastal_zone: CoastalSupplyZone | None = None

    @property
    def total_supply_area_sq_miles(self) -> float:
        total = self.land_zone.square_miles

        if self.river_corridor:
            total += self.river_corridor.square_miles

        if self.coastal_zone:
            total += self.coastal_zone.square_miles

        return total
    
    @property
    def maritime_modifier(self) -> int:
        if self.active_fisheries and self.salt_supply:
            return 2
        return 0

    @property
    def total_supply_area_hectares(self) -> float:
        return self.total_supply_area_sq_miles * HECTARES_PER_SQ_MILE