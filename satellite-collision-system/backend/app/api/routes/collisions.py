from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime
from app.database.session import get_db
from app.database.models import Satellite, PositionHistory
from app.services.collision_detector import CollisionDetector
from app.api.schemas.collision import CollisionResponse
from typing import List

router = APIRouter(prefix="/collisions", tags=["Collisions"])



@router.get("/", response_model=List[CollisionResponse])
def detect_collisions(
    hours_ahead: int = Query(24, ge=1, le=168),
    min_risk: str = Query("LOW"),
    db: Session = Depends(get_db)
):
    detector = CollisionDetector(db)

    rows = (
        db.query(PositionHistory)
        .filter(
            PositionHistory.data_source.in_(["ml_prediction", "actual"])
        )
        .all()
    )

    time_map = {}
    for row in rows:
        time_map.setdefault(row.timestamp, []).append(row)

    collisions = []
    for time_point, sats in time_map.items():
        if len(sats) < 2:
            continue
        collisions.extend(detector.check_all_pairs(sats, time_point))

    risk_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    min_level = risk_order[min_risk.upper()]

    collisions = [
        c for c in collisions
        if c.get("satellite1") and c.get("satellite2")
    ]

    return [
        c for c in collisions
        if risk_order[c["risk_level"]] >= min_level
    ]