import DatabaseService from "./DatabaseService";
import ApiService from "./ApiService";
import { Detection, Species } from "../types";

export default class ListService {
    static async aggregateDetectionsToSpecies(
        detections: Detection[],
    ): Promise<Species[]> {
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

        for (const [commonName, groupedDetections] of speciesMap.entries()) {
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

            const imageUrl = await this.getBirdImage(species);
            species.imageUrl = imageUrl;

            speciesList.push(species);
        }

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

    static async getBirdImage(species: Species): Promise<string> {
        if (!species?.scientificName) {
            return "";
        }

        const pageTitle = encodeURIComponent(
            species.scientificName.trim().replace(/\s+/g, "_"),
        );

        const response = await ApiService.callApi(
            `/api/rest_v1/page/summary/${pageTitle}`,
            undefined,
            "GET",
            undefined,
            "https://en.wikipedia.org",
        );

        if (!response || typeof response !== "object") {
            return "";
        }

        const imageUrl = (response as { originalimage?: { source?: unknown } })
            .originalimage?.source;

        return typeof imageUrl === "string" ? imageUrl : "";
    }

    static async getSpeciesAudioBlob(species: Species): Promise<Blob | null> {
        if (!species?.commonName) {
            return null;
        }

        const birdSongs = await DatabaseService.getAllFromDatabase("birdSongs");
        if (!birdSongs || birdSongs.length === 0) {
            return null;
        }

        const normalizedTargetSpecies = species.commonName.trim().toLowerCase();

        const matchingSongs = birdSongs.filter((song: any) => {
            const songSpecies = String(song?.species ?? "")
                .trim()
                .toLowerCase();
            return songSpecies === normalizedTargetSpecies;
        });

        if (matchingSongs.length === 0) {
            return null;
        }

        const latestSong = matchingSongs.reduce((latest: any, current: any) =>
            Number(current?.timestamp ?? 0) > Number(latest?.timestamp ?? 0)
                ? current
                : latest,
        );

        return latestSong?.audioBlob instanceof Blob ? latestSong.audioBlob : null;
    }
}
