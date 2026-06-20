import DatabaseService from "./DatabaseService";
import ApiService from "./ApiService";
import { Detection, Species } from "../types";

export default class ListService {
    private static readonly WIKI_BASE_URL = "https://en.wikipedia.org";
    private static readonly WIKI_TIMEOUT_MS = 6000;
    private static readonly IMAGE_CACHE_STORAGE_KEY = "birdnet:imageCache:v1";
    private static imageCache = new Map<string, string>();
    private static cacheLoaded = false;

    private static loadImageCacheFromStorage() {
        if (this.cacheLoaded || typeof window === "undefined") {
            return;
        }

        this.cacheLoaded = true;

        try {
            const raw = window.localStorage.getItem(this.IMAGE_CACHE_STORAGE_KEY);
            if (!raw) {
                return;
            }

            const parsed = JSON.parse(raw) as Record<string, string>;
            for (const [key, value] of Object.entries(parsed)) {
                if (typeof value === "string") {
                    this.imageCache.set(key, value);
                }
            }
        } catch {
            // Ignore invalid cache payloads.
        }
    }

    private static persistImageCacheToStorage() {
        if (typeof window === "undefined") {
            return;
        }

        try {
            const payload = JSON.stringify(Object.fromEntries(this.imageCache.entries()));
            window.localStorage.setItem(this.IMAGE_CACHE_STORAGE_KEY, payload);
        } catch {
            // Ignore storage quota/access errors.
        }
    }

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

            let uncommon = false;
            for (const detection of groupedDetections) {
                if (detection.uncommon) {
                    uncommon = true;
                    break;
                }
            }

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
                uncommon: uncommon,
            };

            speciesList.push(species);
        }

        await Promise.all(
            speciesList.map(async (species) => {
                species.imageUrl = await this.getBirdImage(species);
            }),
        );

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

        this.loadImageCacheFromStorage();

        const key = species.scientificName.trim().toLowerCase();
        const cached = this.imageCache.get(key);
        if (cached !== undefined) {
            return cached;
        }

        const pageTitle = encodeURIComponent(
            species.scientificName.trim().replace(/\s+/g, "_"),
        );

        const response = await ApiService.callApi(
            `/api/rest_v1/page/summary/${pageTitle}`,
            undefined,
            "GET",
            undefined,
            this.WIKI_BASE_URL,
            this.WIKI_TIMEOUT_MS,
        );

        if (!response || typeof response !== "object") {
            return "";
        }

        const data = response as {
            originalimage?: { source?: unknown };
            thumbnail?: { source?: unknown };
        };

        const imageUrl = data.originalimage?.source ?? data.thumbnail?.source;
        const finalImageUrl = typeof imageUrl === "string" ? imageUrl : "";
        this.imageCache.set(key, finalImageUrl);
        this.persistImageCacheToStorage();

        return finalImageUrl;
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
