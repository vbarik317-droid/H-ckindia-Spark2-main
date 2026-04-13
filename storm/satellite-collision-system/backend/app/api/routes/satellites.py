from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import Satellite, PositionHistory
from sqlalchemy import or_

router = APIRouter(prefix="/satellites", tags=["Satellites"])


@router.get("/")
def get_satellites(
    db: Session = Depends(get_db),
    limit: int = 300,
    offset: int = 0,
    mode: str = "leo"  # leo | geo | all
):
    query = db.query(Satellite)

    # 🔹 Filter by orbit type
    if mode == "leo":
        query = query.filter(
            or_(
                Satellite.altitude == None,
                Satellite.altitude < 2000
                )
        )
    elif mode == "geo":
        query = query.filter(Satellite.altitude > 30000)

    satellites = (
        query
        .order_by(Satellite.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return satellites