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

    static async getFirstWhere(table: string, predicate: (row: any) => boolean) {
        return await (db as any)[table].filter(predicate).first();
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

    static async putOrOverwrite(table: string, data: any) {
        await (db as any)[table].put(data);
        return true;
    }

    static async saveDetectionFromCloudIfMissing(cloudItem: any) {
        return await this.putIfNotExists("detections", cloudItem.id, {
            id: cloudItem.id,
            date: cloudItem.date,
            time: cloudItem.time,
            scientificName: cloudItem.scientificName,
            commonName: cloudItem.commonName,
            confidence: cloudItem.confidence,
            latitude: cloudItem.latitude,
            longitude: cloudItem.longitude,
            cutoff: cloudItem.cutoff,
            week: cloudItem.week,
            sens: cloudItem.sens,
            overlap: cloudItem.overlap,
            fileName: cloudItem.fileName,
        });
    }

    static async saveSettingFromCloudAndOverwrite(cloudItem: any) {
        return await this.putOrOverwrite("settings", {
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

    static async getBirdSongBySpeciesAndTimestamp(species: string, timestamp: string) {
        return await this.getFirstWhere(
            "birdSongs",
            (row: any) =>
                String(row.species) === String(species) &&
                new Date(row.timestamp).toISOString() === new Date(timestamp).toISOString(),
        );
    }
}
