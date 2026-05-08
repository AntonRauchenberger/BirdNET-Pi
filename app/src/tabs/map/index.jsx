import { useRef, useEffect, useMemo } from "react";
import TabHeader from "../../components/TabHeader";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "../../css/map.css";

const WIFI_ICON_SVG = `
    <svg class="device-marker-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 20h.01"></path>
        <path d="M2 8.82a15 15 0 0 1 20 0"></path>
        <path d="M5 12.86a10 10 0 0 1 14 0"></path>
        <path d="M8.5 16.43a5 5 0 0 1 7 0"></path>
    </svg>
`;

const Map = () => {
    const position = useMemo(() => [49.02, 12.09], []); // [lat, lon]
    const mapContainer = useRef(null);
    const mapRef = useRef(null);

    const MAP_KEY = import.meta.env.VITE_MAP_KEY;

    // Simple openstreet map is used if no key provided, otherwise maptiler with terrain
    const MAP_STYLE = useMemo(
        () =>
            MAP_KEY
                ? `https://api.maptiler.com/maps/outdoor/style.json?key=${MAP_KEY}`
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
        [MAP_KEY],
    );

    useEffect(() => {
        if (mapRef.current) return;

        const map = new maplibregl.Map({
            container: mapContainer.current,
            style: MAP_STYLE,
            center: [position[1], position[0]], // [lon, lat]
            zoom: 13,
        });

        mapRef.current = map;

        map.on("load", () => {
            if (MAP_KEY) {
                try {
                    map.addSource("terrain", {
                        type: "raster-dem",
                        url: `https://api.maptiler.com/tiles/terrain-rgb/tiles.json?key=${MAP_KEY}`,
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

            const markerElement = document.createElement("div");
            markerElement.className = "device-marker";
            markerElement.innerHTML = `<div class="device-marker-pulse"></div><div class="device-marker-core">${WIFI_ICON_SVG}</div>`;

            const popupContent = `
                <article class="device-popup-card">
                    <div class="device-popup-icon" aria-hidden="true">${WIFI_ICON_SVG}</div>
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
    }, [MAP_KEY, MAP_STYLE, position]);

    const styles = {
        mapContainer: {
            position: "fixed",
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
