export function cartesianToLatLonAlt(
  x: number,
  y: number,
  z: number
) {
  const R = Math.sqrt(x * x + y * y + z * z);

  const lat = Math.asin(z / R) * (180 / Math.PI);
  const lon = Math.atan2(y, x) * (180 / Math.PI);
  const alt = R - 6371; // Earth radius in km

  return {
    latitude: lat,
    longitude: lon,
    altitude: alt
  };
}