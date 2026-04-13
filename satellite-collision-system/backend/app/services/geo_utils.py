import numpy as np

def eci_to_latlon(x, y, z):
    r = np.sqrt(x**2 + y**2 + z**2)

    lat = np.arcsin(z / r)
    lon = np.arctan2(y, x)

    return np.degrees(lat), np.degrees(lon)