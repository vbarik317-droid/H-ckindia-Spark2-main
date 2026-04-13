from pydantic import BaseModel
from datetime import datetime
from typing import Tuple, Optional


class CollisionResponse(BaseModel):
    satellite1: str
    satellite2: str
    time: datetime
    distance_km: float
    relative_velocity_kms: float
    probability: float
    risk_level: str
    pos1: Optional[Tuple[float, float, float]]
    pos2: Optional[Tuple[float, float, float]]