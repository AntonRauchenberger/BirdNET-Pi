import { useRef, useEffect, useMemo, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { X } from "lucide-react";

interface LocationMapProps {
    latitude: number;
    longitude: number;
    commonName: string;
    onClose: () => void;
}

const LocationMap = ({
    latitude,
    longitude,
    commonName,
    onClose,
}: LocationMapProps) => {
    const position = useMemo(
        () => [latitude, longitude],
        [latitude, longitude],
    );
    const mapContainer = useRef(null);
    const mapRef = useRef(null);
    const [isClosing, setIsClosing] = useState(false);

    const MAP_KEY = import.meta.env.VITE_MAP_KEY;

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

    const handleClose = () => {
        setIsClosing(true);
        setTimeout(() => {
            onClose();
        }, 300);
    };

    useEffect(() => {
        if (mapRef.current) return;

        const map = new maplibregl.Map({
            container: mapContainer.current,
            style: MAP_STYLE,
            center: [position[1], position[0]], // [lon, lat]
            zoom: 15,
        });

        mapRef.current = map;

        map.on("load", () => {
            const markerElement = document.createElement("div");
            markerElement.style.width = "25px";
            markerElement.style.height = "25px";
            markerElement.style.background = "var(--card)";
            markerElement.style.borderRadius = "50%";
            markerElement.style.display = "flex";
            markerElement.style.alignItems = "center";
            markerElement.style.justifyContent = "center";
            markerElement.style.boxShadow =
                "0 4px 16px -6px oklch(29.5% 0.055 130/0.3)";
            markerElement.style.color = "white";
            markerElement.style.border = "6px solid var(--black-forest)";

            const popupContent = `
                <article style="padding: 10px;">
                    <div style="font-weight: 600; font-size: 15px; color: var(--black-forest);">
                        ${commonName}
                    </div>
                    <div style="font-size: 13px; opacity: 0.7; color: var(--black-forest);">
                        ${latitude.toFixed(4)}, ${longitude.toFixed(4)}
                    </div>
                </article>
            `;

            const birdMarker = new maplibregl.Marker({
                element: markerElement,
                anchor: "center",
            })
                .setLngLat([position[1], position[0]])
                .setPopup(
                    new maplibregl.Popup({
                        offset: 24,
                        closeButton: false,
                    }).setHTML(popupContent),
                )
                .addTo(map);

            birdMarker.togglePopup();
        });

        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, [MAP_KEY, MAP_STYLE, position, commonName, latitude, longitude]);

    const styles = {
        overlay: {
            position: "fixed" as const,
            top: "0",
            left: "0",
            width: "100%",
            height: "100%",
            background: isClosing ? "rgba(0, 0, 0, 0)" : "rgba(0, 0, 0, 0.5)",
            zIndex: "10",
            transition: "background 0.3s ease-out",
        },
        container: {
            position: "fixed" as const,
            top: "0",
            left: "0",
            width: "100%",
            height: "100%",
            zIndex: "11",
            animation: isClosing
                ? "fadeOut 0.3s ease-out forwards"
                : "fadeIn 0.3s ease-out forwards",
        },
        mapContainer: {
            position: "absolute" as const,
            top: "0",
            left: "0",
            width: "100%",
            height: "100%",
        },
        closeButton: {
            position: "absolute" as const,
            top: "20px",
            right: "20px",
            zIndex: "12",
            background: "var(--gradiant-clay)",
            border: "none",
            borderRadius: "50%",
            width: "44px",
            height: "44px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            boxShadow: "var(--shadow-soft)",
            color: "var(--card)",
            transition: "transform 0.2s ease",
        },
    };

    return (
        <>
            <style>{`
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }

                @keyframes fadeOut {
                    from {
                        opacity: 1;
                    }
                    to {
                        opacity: 0;
                    }
                }
            `}</style>
            <div style={styles.overlay} onClick={handleClose}></div>
            <div style={styles.container}>
                <div ref={mapContainer} style={styles.mapContainer} />
                <button
                    style={styles.closeButton}
                    onClick={handleClose}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.transform = "scale(1.05)";
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.transform = "";
                    }}
                >
                    <X size={24} />
                </button>
            </div>
        </>
    );
};

export default LocationMap;
