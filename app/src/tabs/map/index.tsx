import { useRef, useEffect, useMemo, useState } from "react";
import TabHeader from "../../components/TabHeader";
import maplibregl from "maplibre-gl";
import MapService from "../../lib/services/MapService";
import "maplibre-gl/dist/maplibre-gl.css";
import "../../css/map.css";
import SettingsService from "../../lib/services/SettingsService";

const HARD_DRIVE_ICON_SVG = `
    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-hard-drive" aria-hidden="true"><path d="M10 16h.01"></path><path d="M2.212 11.577a2 2 0 0 0-.212.896V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.527a2 2 0 0 0-.212-.896L18.55 5.11A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path><path d="M21.946 12.013H2.054"></path><path d="M6 16h.01"></path></svg>
`;

const Map = () => {
    const position = useMemo(() => [49.02, 12.09], []); // [lat, lon]
    const mapContainer = useRef<HTMLDivElement | null>(null);
    const mapRef = useRef<maplibregl.Map | null>(null);
    const [mapKey, setMapKey] = useState("");
    const [isMapKeyLoaded, setIsMapKeyLoaded] = useState(false);

    useEffect(() => {
        const loadMapKey = async () => {
            try {
                const keySetting =
                    await SettingsService.getSetting("mapTilerApiKey");
                const settingValue = keySetting?.value;
                setMapKey(
                    typeof settingValue === "string" ? settingValue.trim() : "",
                );
            } catch (error) {
                console.error("Error loading mapTilerApiKey setting:", error);
                setMapKey("");
            } finally {
                setIsMapKeyLoaded(true);
            }
        };

        loadMapKey();
    }, []);

    // Simple openstreet map is used if no key provided, otherwise maptiler with terrain
    const MAP_STYLE = useMemo(
        () =>
            mapKey
                ? `https://api.maptiler.com/maps/outdoor/style.json?key=${mapKey}`
                : {
                      version: 8,
                      sources: {
                          osm: {
                              type: "raster",
                              tiles: [
                                  "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                              ],
                              tileSize: 256,
                          },
                      },
                      layers: [
                          {
                              id: "osm-layer",
                              type: "raster",
                              source: "osm",
                          },
                      ],
                  },
        [mapKey],
    );

    useEffect(() => {
        if (!isMapKeyLoaded) return;
        if (mapRef.current) return;
        if (!mapContainer.current) return;

        const map = new maplibregl.Map({
            container: mapContainer.current,
            style: MAP_STYLE as any,
            center: [position[1], position[0]], // [lon, lat]
            zoom: 13,
        });

        mapRef.current = map as any;

        map.on("load", async () => {
            if (mapKey) {
                try {
                    map.addSource("terrain", {
                        type: "raster-dem",
                        url: `https://api.maptiler.com/tiles/terrain-rgb/tiles.json?key=${mapKey}`,
                        tileSize: 256,
                    });

                    map.setTerrain({
                        source: "terrain",
                        exaggeration: 1.5,
                    });

                    map.setPitch(60);
                    map.setBearing(-20);
                } catch (err) {
                    console.warn("Terrain konnte nicht geladen werden:", err);
                }
            }

            // Load and render detections
            try {
                const detections = await MapService.getDetectionsForMap();

                const geojsonData = {
                    type: "FeatureCollection" as const,
                    features: detections.map((detection) => ({
                        type: "Feature" as const,
                        properties: {
                            commonName: detection.commonName,
                            scientificName: detection.scientificName,
                        },
                        geometry: {
                            type: "Point" as const,
                            coordinates: [
                                detection.longitude,
                                detection.latitude,
                            ],
                        },
                    })),
                };

                map.addSource("detections", {
                    type: "geojson",
                    data: geojsonData,
                });

                map.addLayer({
                    id: "detections-layer",
                    type: "circle",
                    source: "detections",
                    paint: {
                        "circle-radius": 3,
                        "circle-color": "rgb(35, 50, 19)",
                        "circle-opacity": 0.6,
                    },
                });
            } catch (err) {
                console.error("Error loading detections:", err);
            }

            // Add legend
            const legendElement = document.createElement("div");
            legendElement.className = "map-legend";
            legendElement.innerHTML = `
                <div style="background: var(--card); padding: 12px; border-radius: 8px; border: var(--card-border); box-shadow: 0 2px 8px rgba(40, 54, 24, 0.1); min-width: 200px; font-size: 13px;">
                    <div style="font-weight: 600; margin-bottom: 8px; color: var(--black-forest);">Legend</div>
                    <div style="display: flex; align-items: center; gap: 3px; margin-bottom: 6px;">
                        <div style="width: 20px; height: 20px; border-radius: 50%; background: var(--copperwood); border: 2px solid var(--card);"></div>
                        <span>Your device</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-left: 6px;">
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--black-forest); opacity: 0.8;"></div>
                        <span>Bird detections</span>
                    </div>
                </div>
            `;
            legendElement.style.position = "absolute";
            legendElement.style.bottom = "100px";
            legendElement.style.right = "20px";
            legendElement.style.zIndex = "100";

            mapContainer.current?.appendChild(legendElement);

            const markerElement = document.createElement("div");
            markerElement.className = "device-marker";
            markerElement.innerHTML = `<div class="device-marker-pulse"></div><div class="device-marker-core"></div>`;

            const popupContent = `
                <article class="device-popup-card">
                    <div class="device-popup-icon" aria-hidden="true">${HARD_DRIVE_ICON_SVG}</div>
                    <div class="device-popup-main">
                        <div class="device-popup-title-row">
                            <strong>Your device</strong>
                        </div>
                        <div class="device-popup-sub">Last sync · 12 min ago</div>
                    </div>
                </article>
            `;

            const deviceMarker = new maplibregl.Marker({
                element: markerElement,
                anchor: "center",
            })
                .setLngLat([position[1], position[0]])
                .setPopup(
                    new maplibregl.Popup({
                        offset: 24,
                        closeButton: false,
                        className: "device-popup",
                    }).setHTML(popupContent),
                )
                .addTo(map);

            deviceMarker.togglePopup();
        });

        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, [isMapKeyLoaded, mapKey, MAP_STYLE, position]);

    const styles = {
        mapContainer: {
            position: "fixed" as const,
            top: "0",
            left: "0",
            width: "100%",
            height: "100%",
        },
    };

    return (
        <div style={{ height: "100vh", width: "100%" }}>
            <TabHeader tab={"DEVICE LOCATION"} title={"Whispering Pines"} />
            <div ref={mapContainer} style={styles.mapContainer} />
        </div>
    );
};

export default Map;
