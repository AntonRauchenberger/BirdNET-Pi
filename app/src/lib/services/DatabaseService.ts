import { db } from "../../db";

export default class DatabaseService {
    static async saveToDatabase(table: string, data: any[]) {
        await (db as any)[table].bulkPut(data);
    }

    static async saveSingleRowToDatabase(table: string, data: any) {
        await (db as any).transaction("rw", (db as any)[table], async () => {
            await (db as any)[table].clear();
            await (db as any)[table].put({ ...data, id: 1 });
        });
    }

    static async getAllFromDatabase(table: string) {
        return await (db as any)[table].toArray();
    }

    static async getSingleRowFromDatabase(table: string) {
        return await (db as any)[table].get(1);
    }

    static async getById(table: string, id: any) {
        return await (db as any)[table].get(id);
    }

    static async putIfNotExists(table: string, id: any, data: any) {
        return await (db as any).transaction("rw", (db as any)[table], async () => {
            const existing = await (db as any)[table].get(id);
            if (existing) {
                return false;
            }

            await (db as any)[table].put(data);
            return true;
        });
    }

    static async saveDetectionFromCloudIfMissing(cloudItem: any) {
        return await this.putIfNotExists("detections", cloudItem.id, {
            id: cloudItem.id,
            Date: cloudItem.Date,
            Time: cloudItem.Time,
            Sci_Name: cloudItem.Sci_Name,
            Com_Name: cloudItem.Com_Name,
            Confidence: cloudItem.Confidence,
            Lat: cloudItem.Lat,
            Lon: cloudItem.Lon,
            Cutoff: cloudItem.Cutoff,
            Week: cloudItem.Week,
            Sens: cloudItem.Sens,
            Overlap: cloudItem.Overlap,
            File_Name: cloudItem.File_Name,
        });
    }

    static async saveSettingFromCloudIfMissing(cloudItem: any) {
        return await this.putIfNotExists("settings", cloudItem.id, {
            id: cloudItem.id,
            name: cloudItem.name,
            description: cloudItem.description,
            value: cloudItem.value,
            tab: cloudItem.tab,
            type: cloudItem.type,
            icon: cloudItem.icon,
            disabled: cloudItem.disabled,
            defaultValue: cloudItem.defaultValue,
        });
    }

    static async saveBirdSongFromCloudIfMissing(song: {
        id: any;
        species: string;
        timestamp: string;
        audioBlob: Blob;
    }) {
        return await this.putIfNotExists("birdSongs", song.id, song);
    }
}
