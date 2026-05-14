import DatabaseService from "./DatabaseService";
import { Detection, Species } from "../types";

export default class ListService {
    static aggregateDetectionsToSpecies(detections: Detection[]): Species[] {
        const speciesMap = new Map<string, Detection[]>();

        // Group detections by commonName
        detections.forEach((detection) => {
            const key = detection.commonName;
            if (!speciesMap.has(key)) {
                speciesMap.set(key, []);
            }
            speciesMap.get(key)!.push(detection);
        });

        // Convert grouped detections to Species
        const speciesList: Species[] = [];

        speciesMap.forEach((groupedDetections, commonName) => {
            const avgConfidence =
                groupedDetections.reduce((sum, d) => sum + d.confidence, 0) /
                groupedDetections.length;

            const scientificNames = [
                ...new Set(groupedDetections.map((d) => d.scientificName)),
            ];
            const scientificName =
                scientificNames.length > 0 ? scientificNames[0] : "Unknown";

            // Find the most recent detection
            const lastDetection = groupedDetections.reduce((latest, current) =>
                current.date > latest.date ? current : latest,
            );

            // Find the first detection
            const firstDetection = groupedDetections.reduce(
                (earliest, current) =>
                    current.date < earliest.date ? current : earliest,
            );

            const species: Species = {
                commonName,
                scientificName,
                avgConfidence: Math.round(avgConfidence * 100),
                detections: groupedDetections.length,
                lastCall: lastDetection.date,
                latitude: lastDetection.latitude,
                longitude: lastDetection.longitude,
                firstSeen: firstDetection.date,
                fileName: lastDetection.fileName,
            };

            speciesList.push(species);
        });

        // Sort by number of detections (descending)
        return speciesList.sort((a, b) => b.detections - a.detections);
    }

    static async getBirdsList(): Promise<Species[]> {
        const allDetections =
            await DatabaseService.getAllFromDatabase("detections");

        if (!allDetections || allDetections.length === 0) {
            return [];
        }

        return this.aggregateDetectionsToSpecies(allDetections);
    }
}
