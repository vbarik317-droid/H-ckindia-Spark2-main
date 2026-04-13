import { useEffect, useRef } from "react";
import * as Cesium from "cesium";

import "cesium/Widgets/widgets.css";
import { Collision } from "../types";

// 🔐 Replace with your real Cesium Ion token
Cesium.Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyMmM3ZWJkOS0zZWRiLTQ3YWItYjI4NC0wNzRjZjVmYmUzNzQiLCJpZCI6MzkxMzQwLCJpYXQiOjE3NzEzMjY5Mjl9.RplI6WBDrTOsTTqUPIZE_p3j9JdNtn6iIjTZ4ytvJ-U";

interface Satellite {
  norad_id: string;
  name: string;
  latitude?: number;
  longitude?: number;
  altitude?: number;
}



interface GlobeProps {
  satellites: Satellite[];
  collisions: Collision[];
  selectedSatellite: Satellite | null;
}

const Globe = ({
  satellites,
  collisions,
  selectedSatellite
}: GlobeProps) => {
  const filteredSatellites = satellites.filter(sat => {
    (sat.altitude ?? 0) < 2000
    // Always show selected satellite
    if (selectedSatellite?.norad_id === sat.norad_id) return true;

    // Show satellites involved in collisions
    if (collisions.some(c =>
      c.satellite1 === sat.norad_id ||
      c.satellite2 === sat.norad_id
    )) return true;

    // Otherwise only show low-earth orbit satellites
    return sat.altitude !== undefined && sat.altitude < 2000;
  });
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);

  // ================================
  // INITIALIZE CESIUM (RUN ONCE)
  // ================================
  useEffect(() => {
    if (!containerRef.current) return;

    const initViewer = async () => {
      const terrainProvider =
        await Cesium.createWorldTerrainAsync();

      const viewer = new Cesium.Viewer(containerRef.current!, {
        animation: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        vrButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        navigationHelpButton: false,
        navigationInstructionsInitiallyVisible: false,
        terrainProvider
      });

      viewer.scene.globe.enableLighting = true;

      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
          0,
          20,
          20000000
        )
      });

      viewerRef.current = viewer;
    };

    initViewer();

    return () => {
      viewerRef.current?.destroy();
      viewerRef.current = null;
    };
  }, []);

  // ================================
  // UPDATE SATELLITES
  // ================================
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    viewer.entities.removeAll();

    // Add satellites
    filteredSatellites.forEach((sat) => {
      if (!sat.latitude || !sat.longitude) return;

      const lat = sat.latitude;
      const lon = sat.longitude;
      
      const alt = (sat.altitude ?? 400) * 1000;

      const isSelected =
        selectedSatellite?.norad_id === sat.norad_id;

      const hasCollision = collisions.some(
        (c) =>
          c.satellite1 === sat.norad_id ||
          c.satellite2 === sat.norad_id
      );

      viewer.entities.add({
        id: sat.norad_id,
        name: sat.name,
        position: Cesium.Cartesian3.fromDegrees(
          lon,
          lat,
          alt
        ),
        point: {
          pixelSize: isSelected ? 12 : 8,
          color: hasCollision
            ? Cesium.Color.RED
            : isSelected
            ? Cesium.Color.BLUE
            : Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 1
        },
        label: {
          text: sat.name,
          font: "12px sans-serif",
          fillColor: Cesium.Color.WHITE,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          outlineWidth: 2,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -20),
          show: isSelected || hasCollision
        }
      });
    });

    // ================================
    // DRAW COLLISION LINES (ML-BASED)
    // ================================
    collisions.forEach((collision) => {
      const { pos1, pos2, risk_level } = collision;

      if (!pos1 || !pos2) return;

      const color =
        risk_level === "HIGH"
          ? Cesium.Color.RED
          : risk_level === "MEDIUM"
          ? Cesium.Color.ORANGE
          : Cesium.Color.YELLOW;

      const glow =
        risk_level === "HIGH" ? 0.4 : 0.15;

      viewer.entities.add({
        polyline: {
          positions: [
            Cesium.Cartesian3.fromDegrees(
              pos1.lon,
              pos1.lat,
              pos1.alt * 1000
            ),
            Cesium.Cartesian3.fromDegrees(
              pos2.lon,
              pos2.lat,
              pos2.alt * 1000
            )
          ],
          width: risk_level === "HIGH" ? 4 : 2,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: new Cesium.CallbackProperty(
              () => 0.2 + Math.abs(Math.sin(Date.now() / 500)) * 0.3,
              false
            ),
            color
          })
        }
      });
    });

    // Fly to selected
    if (selectedSatellite) {
      const entity = viewer.entities.getById(
        selectedSatellite.norad_id
      );
      if (entity) viewer.flyTo(entity);
    }
  }, [satellites, collisions, selectedSatellite]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%" }}
    />
  );
};

export default Globe;