import { db } from "../../db";

export default class DatabaseService {
    static async saveToDatabase(table: string, data: any[]) {
        await (db as any)[table].bulkPut(data);
    }

    static async getAllFromDatabase(table: string) {
        return await (db as any)[table].toArray();
    }
}
