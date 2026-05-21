import { createClient } from "@supabase/supabase-js";
import SettingsService from "./SettingsService";
import DatabaseService from "./DatabaseService";
import { Detection, Setting } from "../types";

export default class CloudService {
    static normalizeSettingValue(value: any, type?: string) {
        if (value === undefined || value === null) {
            return "";
        }

        if (type === "boolean") {
            if (typeof value === "boolean") {
                return value ? "true" : "false";
            }

            const normalized = String(value).trim().toLowerCase();
            if (normalized === "true" || normalized === "1") {
                return "true";
            }
            if (normalized === "false" || normalized === "0") {
                return "false";
            }
        }

        return String(value).trim();
    }

    static buildSongKey(species: string, timestamp: any) {
        return `${String(species).trim().toLowerCase()}|${new Date(timestamp).toISOString()}`;
    }

    static async getSupabaseClient() {
        const urlSetting = await SettingsService.getSetting("supabaseUrl");
        const keySetting = await SettingsService.getSetting("supabaseKey");

        if (!urlSetting?.value || !keySetting?.value) {
            throw new Error("Missing Supabase credentials");
        }

        return createClient(String(urlSetting.value), String(keySetting.value));
    }

    static mapData(data: Setting | Detection, tableName: string) {
        let normalizedData: any;
        switch (tableName) {
            case "detections":
                normalizedData = data as Detection;

                return {
                    id: normalizedData.id,
                    date: normalizedData.date,
                    time: normalizedData.time,
                    scientificName: normalizedData.scientificName,
                    commonName: normalizedData.commonName,
                    confidence: normalizedData.confidence,
                    latitude: normalizedData.latitude,
                    longitude: normalizedData.longitude,
                    cutoff: normalizedData.cutoff,
                    week: normalizedData.week,
                    sens: normalizedData.sens,
                    overlap: normalizedData.overlap,
                    fileName: normalizedData.fileName,
                };
            case "settings":
                normalizedData = data as Setting;

                return {
                    id: normalizedData.id,
                    name: normalizedData.name,
                    description: normalizedData.description,
                    value: normalizedData.value,
                    tab: normalizedData.tab,
                    type: normalizedData.type,
                    icon: normalizedData.icon ? normalizedData.icon.toString() : null,
                    disabled: normalizedData.disabled,
                    defaultValue: normalizedData.defaultValue,
                };
            case "bird_songs":
                normalizedData = data as Detection;

                return {
                    id: normalizedData.id,
                    species: normalizedData.species,
                    timestamp: normalizedData.timestamp,
                    audio_url: normalizedData.audio_url,
                };
            default:
                throw new Error(`Unknown table name: ${tableName}`);
        }
    }

    static async syncTable(supabase: any, tableName: string) {
        const data = await DatabaseService.getAllFromDatabase(tableName);
        if (data.length === 0) {
            console.log(`No ${tableName} to sync`);
            return;
        }

        const filteredData =
            tableName === "settings"
                ? data.filter((item: any) => {
                    const currentValue = this.normalizeSettingValue(item.value, item.type);
                    const defaultValue = this.normalizeSettingValue(item.defaultValue, item.type);
                    return currentValue !== defaultValue;
                })
                : data;

        if (filteredData.length === 0) {
            console.log(`No changed ${tableName} to sync`);
            return;
        }

        const mappedData = filteredData.map((item: any) => this.mapData(item, tableName));

        const { error } = await supabase.from(tableName).upsert(mappedData, {
            onConflict: "id",
        });

        if (error) {
            throw error;
        }

        console.log(`${tableName} synced to Supabase successfully`);
    }

    static async syncAudioFiles(supabase: any) {
        const localSongs = await DatabaseService.getAllFromDatabase("birdSongs");

        if (localSongs.length === 0) {
            console.log("No audio files to sync");
            return;
        }

        const { data: cloudSongs, error: cloudSongsError } = await supabase
            .from("bird_songs")
            .select("species,timestamp");

        if (cloudSongsError) {
            throw cloudSongsError;
        }

        const existingCloudKeys = new Set(
            (cloudSongs || []).map((song: any) => this.buildSongKey(song.species, song.timestamp)),
        );
        const processedLocalKeys = new Set<string>();

        for (const song of localSongs) {
            if (!song.audioBlob) {
                continue;
            }

            const songKey = this.buildSongKey(song.species, song.timestamp);
            if (processedLocalKeys.has(songKey) || existingCloudKeys.has(songKey)) {
                continue;
            }

            processedLocalKeys.add(songKey);

            const normalizedTimestamp = new Date(song.timestamp).toISOString();

            // Generate a clean filename using the song ID and species name
            const cleanSpecies = song.species.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase();
            const safeTimestamp = normalizedTimestamp
                .replace(/[:.]/g, "-")
                .replace(/[^a-zA-Z0-9_-]/g, "_");
            const fileName = `${cleanSpecies}_${safeTimestamp}.wav`;

            // Upload the audio blob to Supabase Storage
            const { error: storageError } = await supabase
                .storage
                .from("bird-audio")
                .upload(fileName, song.audioBlob, {
                    contentType: "audio/wav",
                    upsert: true
                });

            if (storageError) {
                console.error(`Error uploading ${fileName}:`, storageError);
                continue;
            }

            // Get the public URL for the uploaded file
            const { data: urlData } = supabase
                .storage
                .from("bird-audio")
                .getPublicUrl(fileName);

            const publicAudioUrl = urlData.publicUrl;

            // Save metadata bird_songs Supabase table including the public URL
            const { error: dbError } = await supabase
                .from("bird_songs")
                .insert({
                    species: song.species,
                    timestamp: normalizedTimestamp,
                    audio_url: publicAudioUrl // Hier verknüpfen wir SQL mit Storage!
                });

            if (dbError) {
                console.error(`Error saving metadata for ${fileName}:`, dbError);
                continue;
            }

            existingCloudKeys.add(songKey);

            console.log(`Audio file ${fileName} uploaded and metadata saved successfully`);
        }
    }

    static async syncToSupabase() {
        try {
            const supabase = await this.getSupabaseClient();

            await this.syncTable(supabase, "detections");
            await this.syncTable(supabase, "settings");
            await this.syncAudioFiles(supabase);

        } catch (error) {
            console.error("Error syncing to Supabase:", error);
        }
    }

    static async downloadDetectionsFromSupabase(supabase: any) {
        const { data: cloudDetections, error } = await supabase
            .from("detections")
            .select("*");

        if (error) {
            throw error;
        }

        if (!cloudDetections || cloudDetections.length === 0) {
            console.log("No detections found in Supabase");
            return;
        }

        for (const cloudItem of cloudDetections) {
            const inserted = await DatabaseService.saveDetectionFromCloudIfMissing(cloudItem);

            if (inserted) {
                console.log(`Entry ${cloudItem.id} loaded from cloud.`);
            } else {
                // Entry already exists, skip it to protect local data integrity
                console.log(`Entry ${cloudItem.id} already exists locally. Skipping (Protection active).`);
            }
        }
    }

    static async downloadAllSettingsFromSupabase(supabase: any) {
        const { data: cloudSettings, error } = await supabase
            .from("settings")
            .select("*");

        if (error) {
            throw error;
        }

        if (!cloudSettings || cloudSettings.length === 0) {
            console.log("No settings found in Supabase");
            return;
        }

        for (const cloudItem of cloudSettings) {
            const inserted = await DatabaseService.saveSettingFromCloudAndOverwrite(cloudItem);

            if (inserted) {
                console.log(`Entry ${cloudItem.id} loaded from cloud.`);
            } else {
                // Entry already exists, skip it to protect local data integrity
                console.log(`Entry ${cloudItem.id} already exists locally. Skipping (Protection active).`);
            }
        }
    }

    static async downloadBirdSongsFromCloud(supabase: any) {
        try {
            const { data: cloudSongs, error } = await supabase
                .from("bird_songs")
                .select("*");

            if (error) {
                throw error;
            };

            if (!cloudSongs || cloudSongs.length === 0) {
                console.log("No bird songs found in Supabase");
                return;
            }

            for (const cloudSong of cloudSongs) {
                if (!cloudSong.audio_url) {
                    console.log(`Song ${cloudSong.id} has no audio_url. Skipping.`);
                    continue;
                }

                // Use species+timestamp for deduplication because local and cloud IDs are not guaranteed to match.
                const localSong = await DatabaseService.getBirdSongBySpeciesAndTimestamp(
                    cloudSong.species,
                    cloudSong.timestamp,
                );

                if (!localSong) {
                    // Song doesn't exist locally yet, download audio file from storage
                    console.log(`Downloading audio for song ${cloudSong.id}...`);

                    try {
                        const response = await fetch(cloudSong.audio_url);
                        if (!response.ok) {
                            throw new Error("Audio download from URL failed");
                        }

                        // Convert file to binary object (Blob)
                        const audioBlob = await response.blob();

                        const newEntry = {
                            id: cloudSong.id,
                            species: cloudSong.species,
                            timestamp: cloudSong.timestamp,
                            audioBlob: audioBlob
                        }
                        const inserted = await DatabaseService.saveBirdSongFromCloudIfMissing(newEntry);

                        if (!inserted) {
                            console.log(`Song ${cloudSong.id} already exists locally. Skipping.`);
                            continue;
                        }

                        console.log(`Song ${cloudSong.id} successfully made available offline.`);
                    } catch (fetchErr) {
                        console.error(`Could not load audio for song ${cloudSong.id}:`, fetchErr);
                    }
                } else {
                    // Song already exists, leave it completely untouched
                    console.log(`Song ${cloudSong.id} already exists locally. Skipping.`);
                }
            }

            console.log("All cloud songs processed.");

        } catch (error) {
            console.error("Error during audio download:", error);
        }
    }

    static async fetchFromSupabase() {
        try {
            const supabase = await this.getSupabaseClient();

            await this.downloadDetectionsFromSupabase(supabase);
            await this.downloadAllSettingsFromSupabase(supabase);
            await this.downloadBirdSongsFromCloud(supabase);

        } catch (error) {
            console.error("Error fetching from Supabase:", error);
        }
    }
}