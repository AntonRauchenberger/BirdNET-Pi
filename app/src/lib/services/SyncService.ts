import ApiService from "./ApiService";
import DatabaseService from "./DatabaseService";
import { SYNC_ROW_LIMIT } from "../constants";
import { Detection } from "../types";

export default class SyncService {
    static async getPendingDetectionsAmount() {
        const responseData = await ApiService.callApi(
            "/sync/pendingdetectionsamount",
        );

        if (responseData === false || !responseData?.amount) {
            return false;
        }

        return responseData.amount;
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
        };
    }

    static async saveSyncData(data: Detection[]) {
        await DatabaseService.saveToDatabase("detections", data);
    }

    static async syncData(
        offset: number,
        limit: number = SYNC_ROW_LIMIT,
    ): Promise<boolean> {
        const rawData = await this.getSyncData(offset, limit);
        if (rawData === false) {
            return false;
        }

        const detections: Detection[] = rawData.map(this.mapRowToDetection);
        await this.saveSyncData(detections);
        return true;
    }

    static async markDataAsSynced(
        offset: number,
        limit: number = SYNC_ROW_LIMIT,
    ) {
        // TODO implementieren
        // TODO auch Einstellung einbauen, ob die Daten nach dem Syncen gelöscht werden sollen oder nicht
    }
}
