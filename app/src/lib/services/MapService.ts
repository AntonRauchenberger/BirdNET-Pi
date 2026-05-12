import DatabaseService from "./DatabaseService,";
import { Detection } from "../types";

export default class MapService {
    static async getDetectionsForMap(): Promise<Detection[]> {
        const allDetections =
            await DatabaseService.getAllFromDatabase("detections");
        return allDetections || [];
    }
}
