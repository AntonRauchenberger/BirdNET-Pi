import ApiService from "./ApiService";
import DatabaseService from "./DatabaseService";
import { SYNC_ROW_LIMIT } from "../constants";
import { Detection } from "../types";
import SettingsService from "./SettingsService";

export default class SyncService {
    private static asBoolean(value: unknown): boolean {
        if (typeof value === "boolean") {
            return value;
        }

        if (typeof value === "string") {
            const normalized = value.trim().toLowerCase();
            return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
        }

        if (typeof value === "number") {
            return value !== 0;
        }

        return false;
    }

    static async getPendingDetectionsAmount() {
        const responseData = await ApiService.callApi(
            "/sync/pendingdetectionsamount",
        );

        if (
            responseData === false ||
            typeof responseData?.detectionsAmount !== "number" ||
            typeof responseData?.speciesAmount !== "number"
        ) {
            return false;
        }

        return responseData;
    }

    static async getSyncData(offset: number, limit: number = SYNC_ROW_LIMIT) {
        const responseData = await ApiService.callApi("/sync/data", {
            offset,
            limit,
        });
        if (responseData === false) {
            return false;
        }

        return responseData;
    }

    static mapRowToDetection(row: any): Detection {
        return {
            date: row.date,
            time: row.time,
            scientificName: row.sci_name,
            commonName: row.com_name,
            confidence: row.confidence,
            latitude: row.lat,
            longitude: row.lon,
            cutoff: row.cutoff,
            week: row.weekday,
            sens: row.sens,
            overlap: row.overlap,
            fileName: row.file_name,
            uncommon: row?.uncommon || false,
        };
    }

    static async saveSyncData(data: Detection[]) {
        await DatabaseService.saveToDatabase("detections", data);
    }

    static async syncData(
        offset: number,
        limit: number = SYNC_ROW_LIMIT,
    ): Promise<number | false> {
        const rawData = await this.getSyncData(offset, limit);
        if (rawData === false) {
            return false;
        }

        const detections: Detection[] = rawData.map(this.mapRowToDetection);
        await this.saveSyncData(detections);
        return detections.length;
    }

    static async syncAudioFiles(speciesComName: string): Promise<boolean> {
        const rawData = await ApiService.getAudioFile(`/sync/audiofile`, {
            species_com_name: speciesComName,
        });

        // No audio exists for this species on the device yet; skip gracefully.
        if (rawData === null) {
            return true;
        }

        if (rawData === false) {
            return false;
        }

        const audioBlob = await rawData.blob();
        const birdSongEntry = {
            species: speciesComName,
            timestamp: Date.now(),
            audioBlob,
        };

        await DatabaseService.saveToDatabase("birdSongs", [birdSongEntry]);
        return true;
    }

    static async deleteSyncedData(): Promise<boolean> {
        const deleteSyncedDataSetting =
            await SettingsService.getSetting("deleteSyncedData");
        if (!this.asBoolean(deleteSyncedDataSetting?.value)) {
            return true;
        }

        const response = await ApiService.callApi(
            "/sync/deletesynceddata",
            {},
            "DELETE",
        );
        return response !== false;
    }
}
