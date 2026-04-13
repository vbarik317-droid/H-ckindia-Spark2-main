"""
Collision detection module for satellite proximity analysis
"""
import math
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class CollisionDetector:
    """
    Detect potential collisions between space objects
    """

    def __init__(self, db_session, threshold_km: float = 5000.0):
        self.db = db_session
        self.threshold_km = threshold_km

    # --------------------------------------------------
    # Geometry helpers
    # --------------------------------------------------

    def calculate_distance(
        self,
        pos1: Tuple[float, float, float],
        pos2: Tuple[float, float, float],
    ) -> float:
        """Euclidean distance in km"""
        return math.sqrt(
            (pos2[0] - pos1[0]) ** 2
            + (pos2[1] - pos1[1]) ** 2
            + (pos2[2] - pos1[2]) ** 2
        )

    def calculate_relative_velocity(
        self,
        vel1: Tuple[float, float, float],
        vel2: Tuple[float, float, float],
    ) -> float:
        """Relative velocity magnitude (km/s)"""
        return math.sqrt(
            (vel2[0] - vel1[0]) ** 2
            + (vel2[1] - vel1[1]) ** 2
            + (vel2[2] - vel1[2]) ** 2
        )

    # --------------------------------------------------
    # Risk model
    # --------------------------------------------------

    def calculate_collision_probability(
        self,
        distance: float,
        rel_velocity: float,
        object_size1: float = 5.0,
        object_size2: float = 5.0,
    ) -> float:
        """
        Simplified probability model
        """
        combined_radius_km = (object_size1 + object_size2) / 2000.0

        if distance <= combined_radius_km:
            return 1.0

        if distance < self.threshold_km:
            prob = 1.0 - (distance / self.threshold_km)
            velocity_factor = min(rel_velocity / 10.0, 1.0)
            return min(prob * (0.5 + 0.5 * velocity_factor), 0.99)

        return 0.0

    def get_risk_level(self, probability: float) -> str:
        if probability >= 0.7:
            return "HIGH"
        elif probability >= 0.3:
            return "MEDIUM"
        elif probability > 0:
            return "LOW"
        return "NONE"

    # --------------------------------------------------
    # Core collision logic
    # --------------------------------------------------

    def check_pair_collision(self, sat1, sat2, time_point: datetime) -> Dict:
        """
        Check collision between two satellites at a specific time
        """

        # ✅ Positions (EXIST in DB)
        pos1 = (sat1.pos_x, sat1.pos_y, sat1.pos_z)
        pos2 = (sat2.pos_x, sat2.pos_y, sat2.pos_z)

        distance = self.calculate_distance(pos1, pos2)

        # ✅ Velocity NOT stored → assume zero
        vel1 = (0.0, 0.0, 0.0)
        vel2 = (0.0, 0.0, 0.0)

        rel_velocity = self.calculate_relative_velocity(vel1, vel2)

        probability = self.calculate_collision_probability(
            distance, rel_velocity
        )

        risk_level = self.get_risk_level(probability)
        # 🚨 SAFETY CHECK (CRITICAL)
        if not sat1.norad_id or not sat2.norad_id:
            return None

        return {
            'satellite1': sat1.norad_id,
            'satellite2': sat2.norad_id,
            'time': time_point,
            'distance_km': distance,
            'relative_velocity_kms': rel_velocity,
            'probability': probability,
            'risk_level': risk_level,
            'pos1_x': pos1[0],
            'pos1_y': pos1[1],
            'pos1_z': pos1[2],
            'pos2_x': pos2[0],
            'pos2_y': pos2[1],
            'pos2_z': pos2[2],
        }

    def check_all_pairs(
        self, satellites: List, time_point: datetime
    ) -> List[Dict]:
        """
        Check all satellite pairs
        """
        collisions: List[Dict] = []

        for i in range(len(satellites)):
            for j in range(i + 1, len(satellites)):
                result = self.check_pair_collision(
                    satellites[i], satellites[j], time_point
                )

                if result and result["probability"] > 0:
                    collisions.append(result)

                    if result["risk_level"] == "HIGH":
                        logger.warning(
                            f"HIGH RISK: {satellites[i].norad_id} ↔ {satellites[j].norad_id} "
                            f"distance={result['distance_km']} km"
                        )

        return collisions