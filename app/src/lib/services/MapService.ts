import DatabaseService from "./DatabaseService";
import { Detection } from "../types";
import DeviceService from "./DeviceService";

export default class MapService {
    private static hasValidCoordinates(
        latitude: unknown,
        longitude: unknown,
    ): boolean {
        return (
            typeof latitude === "number" &&
            typeof longitude === "number" &&
            Number.isFinite(latitude) &&
            Number.isFinite(longitude) &&
            latitude >= -90 &&
            latitude <= 90 &&
            longitude >= -180 &&
            longitude <= 180
        );
    }

    static async getDetectionsForMap(): Promise<Detection[]> {
        const allDetections =
            await DatabaseService.getAllFromDatabase("detections");
        return allDetections || [];
    }

    static async getLatestDeviceLocation(): Promise<{
        latitude: number;
        longitude: number;
        lastUpdate?: string;
    } | null> {
        const fetchedDeviceInfo = await DeviceService.getDeviceDetails();
        const fetchedLatitude = fetchedDeviceInfo.latitude;
        const fetchedLongitude = fetchedDeviceInfo.longitude;
        if (this.hasValidCoordinates(fetchedLatitude, fetchedLongitude)) {
            return {
                latitude: Number(fetchedLatitude),
                longitude: Number(fetchedLongitude),
                lastUpdate: fetchedDeviceInfo.lastUpdate,
            };
        }

        const cachedDeviceInfo = await DatabaseService.getSingleRowFromDatabase(
            "lastKnownDeviceInfo",
        );

        if (
            cachedDeviceInfo &&
            this.hasValidCoordinates(
                cachedDeviceInfo.latitude,
                cachedDeviceInfo.longitude,
            )
        ) {
            return {
                latitude: Number(cachedDeviceInfo.latitude),
                longitude: Number(cachedDeviceInfo.longitude),
                lastUpdate:
                    typeof cachedDeviceInfo.lastUpdate === "string"
                        ? cachedDeviceInfo.lastUpdate
                        : undefined,
            };
        }

        return null;
    }
}
