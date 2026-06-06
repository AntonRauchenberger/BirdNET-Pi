import { useRef, useEffect, useMemo, useState } from "react";
import TabHeader from "../../components/TabHeader";
import LoadingSpinner from "../../components/LoadingSpinner";
import maplibregl from "maplibre-gl";
import MapService from "../../lib/services/MapService";
import "maplibre-gl/dist/maplibre-gl.css";
import "../../css/map.css";
import SettingsService from "../../lib/services/SettingsService";
import ListService from "../../lib/services/ListService";

const HARD_DRIVE_ICON_SVG = `
    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-hard-drive" aria-hidden="true"><path d="M10 16h.01"></path><path d="M2.212 11.577a2 2 0 0 0-.212.896V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.527a2 2 0 0 0-.212-.896L18.55 5.11A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path><path d="M21.946 12.013H2.054"></path><path d="M6 16h.01"></path></svg>
`;

const BIRD_ICON_SVG = `
    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 7h.01"></path><path d="M3.4 18A4.5 4.5 0 0 1 2 14.5c0-1.8 1-3.6 2.7-4.6A7.7 7.7 0 0 1 12 3c3.3 0 6.1 2 7.2 4.9A4.7 4.7 0 0 1 22 12c0 2.5-1.9 4.6-4.4 5"></path><path d="M2 19c0 1.1.9 2 2 2h8"></path><path d="M13 21c0-1.3.8-2.4 2-2.8"></path><path d="M21 15c0 1.5-1 2.8-2.4 3.2"></path></svg>
`;

const escapeHtml = (value: string): string =>
    value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");

const createDetectionPopupContent = (
    commonName: string,
    scientificName: string,
    imageUrl = "",
): string => {
    const safeCommonName = escapeHtml(commonName || "Unknown detection");
    const safeScientificName = escapeHtml(scientificName || "Unknown species");
    const safeImageUrl = escapeHtml(imageUrl);

    const imageContent = safeImageUrl
        ? `<img src="${safeImageUrl}" alt="${safeCommonName}" class="detection-popup-image" />`
        : `<div class="detection-popup-image-fallback" aria-hidden="true">${BIRD_ICON_SVG}</div>`;

    return `
        <article class="detection-popup-card">
            <div class="detection-popup-image-wrap">${imageContent}</div>
            <div class="detection-popup-main">
                <div class="detection-popup-label">DETECTION</div>
                <div class="detection-popup-title">${safeCommonName}</div>
                <div class="detection-popup-sub">${safeScientificName}</div>
            </div>
        </article>
    `;
};

const formatLastUpdate = (lastUpdate?: string): string => {
    if (!lastUpdate) {
        return "not yet";
    }

    const updatedAt = new Date(lastUpdate);
    if (Number.isNaN(updatedAt.getTime())) {
        return "not yet";
    }

    const diffMs = Date.now() - updatedAt.getTime();
    if (diffMs < 0) {
        return "just now";
    }

    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    if (diffMinutes < 1) {
        return "just now";
    }

    if (diffMinutes < 60 * 24) {
        return `${diffMinutes} min ago`;
    }

    const diffDays = Math.floor(diffMinutes / (60 * 24));
    return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
};

const Map = () => {
    const mapContainer = useRef<HTMLDivElement | null>(null);
    const mapRef = useRef<maplibregl.Map | null>(null);
    const detectionPopupRef = useRef<maplibregl.Popup | null>(null);
    const birdImageCacheRef = useRef<globalThis.Map<string, string>>(
        new globalThis.Map(),
    );
    const [mapKey, setMapKey] = useState("");
    const [deviceLocation, setDeviceLocation] = useState<{
        latitude: number;
        longitude: number;
        lastUpdate?: string;
    } | null>(null);
    const [isMapKeyLoaded, setIsMapKeyLoaded] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadMapData = async () => {
            try {
                const keySetting =
                    await SettingsService.getSetting("mapTilerApiKey");
                const settingValue = keySetting?.value;
                setMapKey(
                    typeof settingValue === "string" ? settingValue.trim() : "",
                );

                const latestDeviceLocation =
                    await MapService.getLatestDeviceLocation();
                setDeviceLocation(latestDeviceLocation);
            } catch (error) {
                console.error("Error loading mapTilerApiKey setting:", error);
                setMapKey("");
            } finally {
                setIsMapKeyLoaded(true);
            }
        };

        loadMapData();
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
            center: deviceLocation
                ? [deviceLocation.longitude, deviceLocation.latitude]
                : [12.0974869, 49.0195333],
            zoom: 13,
        });

        mapRef.current = map as any;

        map.on("load", async () => {
            try {
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
                        console.warn(
                            "Terrain konnte nicht geladen werden:",
                            err,
                        );
                    }
                }

                // Load and render detections
                try {
                    const detections = await MapService.getDetectionsForMap();
                    const limitedDetections = [...detections]
                        .sort((a, b) => b.date - a.date)
                        .slice(0, 300);

                    const geojsonData = {
                        type: "FeatureCollection" as const,
                        features: limitedDetections.map((detection) => ({
                            type: "Feature" as const,
                            properties: {
                                commonName: detection.commonName,
                                scientificName: detection.scientificName,
                                confidence: Math.round(detection.confidence * 100),
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
                        generateId: true,
                        data: geojsonData,
                    });

                    map.addLayer({
                        id: "detections-layer-halo",
                        type: "circle",
                        source: "detections",
                        paint: {
                            "circle-radius": 6,
                            "circle-color": "rgba(40, 54, 24, 0.35)",
                            "circle-opacity": 0.55,
                        },
                    });

                    map.addLayer({
                        id: "detections-layer",
                        type: "circle",
                        source: "detections",
                        paint: {
                            "circle-radius": 4,
                            "circle-color": "rgb(62, 83, 34)",
                            "circle-stroke-width": 1.4,
                            "circle-stroke-color": "rgba(249, 246, 237, 0.85)",
                            "circle-opacity": 0.9,
                        },
                    });

                    map.on("click", "detections-layer", async (event) => {
                        const feature = event.features?.[0];
                        if (!feature) {
                            return;
                        }

                        const coordinates = (
                            feature.geometry as GeoJSON.Point
                        ).coordinates.slice() as [number, number];

                        const commonName =
                            typeof feature.properties?.commonName === "string"
                                ? feature.properties.commonName
                                : "Unknown detection";
                        const scientificName =
                            typeof feature.properties?.scientificName === "string"
                                ? feature.properties.scientificName
                                : "Unknown species";

                        detectionPopupRef.current?.remove();

                        const popup = new maplibregl.Popup({
                            offset: 20,
                            closeButton: false,
                            className: "detection-popup",
                            maxWidth: "340px",
                        })
                            .setLngLat(coordinates)
                            .setHTML(
                                createDetectionPopupContent(
                                    commonName,
                                    scientificName,
                                ),
                            )
                            .addTo(map);

                        detectionPopupRef.current = popup;

                        const cacheKey = scientificName.trim().toLowerCase();
                        const cachedImage = birdImageCacheRef.current.get(cacheKey);

                        if (cachedImage !== undefined) {
                            popup.setHTML(
                                createDetectionPopupContent(
                                    commonName,
                                    scientificName,
                                    cachedImage,
                                ),
                            );
                            return;
                        }

                        try {
                            const imageUrl = await ListService.getBirdImage({
                                commonName,
                                scientificName,
                                avgConfidence: 0,
                                detections: 0,
                                lastCall: 0,
                                latitude: coordinates[1],
                                longitude: coordinates[0],
                                firstSeen: 0,
                                fileName: "",
                            });

                            birdImageCacheRef.current.set(cacheKey, imageUrl);

                            // Prevent stale async updates if another marker was selected in the meantime.
                            if (detectionPopupRef.current === popup) {
                                popup.setHTML(
                                    createDetectionPopupContent(
                                        commonName,
                                        scientificName,
                                        imageUrl,
                                    ),
                                );
                            }
                        } catch (error) {
                            console.error(
                                "Error while loading bird image for map popup:",
                                error,
                            );
                        }
                    });

                    map.on("click", (event) => {
                        const eventTarget = event.originalEvent.target as HTMLElement;
                        if (eventTarget.closest(".detection-popup")) {
                            return;
                        }

                        const featuresAtClick = map.queryRenderedFeatures(
                            event.point,
                            {
                                layers: ["detections-layer"],
                            },
                        );

                        if (featuresAtClick.length === 0) {
                            detectionPopupRef.current?.remove();
                            detectionPopupRef.current = null;
                        }
                    });

                    map.on("mouseenter", "detections-layer", () => {
                        map.getCanvas().style.cursor = "pointer";
                    });

                    map.on("mouseleave", "detections-layer", () => {
                        map.getCanvas().style.cursor = "";
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
                            <div class="device-popup-sub">Updated ${formatLastUpdate(deviceLocation?.lastUpdate)}</div>
                        </div>
                    </article>
                `;

                const deviceMarker = new maplibregl.Marker({
                    element: markerElement,
                    anchor: "center",
                })
                    .setLngLat(
                        deviceLocation
                            ? [
                                deviceLocation.longitude,
                                deviceLocation.latitude,
                            ]
                            : [12.0974869, 49.0195333],
                    )
                    .setPopup(
                        new maplibregl.Popup({
                            offset: 24,
                            closeButton: false,
                            className: "device-popup",
                        }).setHTML(popupContent),
                    )
                    .addTo(map);

                deviceMarker.togglePopup();
            } finally {
                setIsLoading(false);
            }
        });

        return () => {
            detectionPopupRef.current?.remove();
            detectionPopupRef.current = null;
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, [isMapKeyLoaded, mapKey, MAP_STYLE, deviceLocation]);

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
        <div style={{ height: "100vh", width: "100%", position: "relative" }}>
            <div className={isLoading ? "loading-content-blurred" : ""}>
                <TabHeader tab={"DEVICE LOCATION"} title={"Whispering Pines"} />
                <div ref={mapContainer} style={styles.mapContainer} />
            </div>
            {isLoading && <LoadingSpinner />}
        </div>
    );
};

export default Map;
