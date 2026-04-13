from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import CollisionEvent
from datetime import datetime, timedelta

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/")
def get_alerts(
    hours_back: int = 24,
    min_risk: str = "LOW",
    db: Session = Depends(get_db)
):
    since = datetime.utcnow() - timedelta(hours=hours_back)

    query = db.query(CollisionEvent).filter(
        CollisionEvent.predicted_time >= since
    )

    if min_risk != "LOW":
        query = query.filter(CollisionEvent.risk_level == min_risk)

    return query.order_by(CollisionEvent.predicted_time.desc()).all()