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
}
