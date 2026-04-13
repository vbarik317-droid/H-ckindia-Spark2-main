from sgp4.api import Satrec
from sgp4.api import jday
from datetime import datetime
import numpy as np

def propagate_tle(tle_line1, tle_line2):
    """
    Propagate satellite using SGP4
    Returns position (km) and velocity (km/s)
    """

    satellite = Satrec.twoline2rv(tle_line1, tle_line2)

    now = datetime.utcnow()
    jd, fr = jday(
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        now.second + now.microsecond * 1e-6
    )

    e, r, v = satellite.sgp4(jd, fr)

    if e != 0:
        return None

    return r, v  # r = (x,y,z), v = velocity