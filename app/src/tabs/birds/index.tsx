import { useEffect, useState } from "react";
import TabHeader from "../../components/TabHeader";
import { Species } from "../../lib/types";
import Filters from "./Filters";
import SpeciesListItem from "./SpeciesListItem";
import SpeciesDetails from "./SpeciesDetails";
import ListService from "../../lib/services/ListService";
import LoadingSpinner from "../../components/LoadingSpinner";
import SettingsService from "../../lib/services/SettingsService";
import CloudService from "../../lib/services/CloudService";
import SyncButtons from "./SyncButtons";

const Birds = () => {
    const [species, setSpecies] = useState<Species[]>([]);
    const [filter, setFilter] = useState<{
        searchInput: string;
        alphabeticSort: null | "asc" | "desc";
        confidenceSort: null | "asc" | "desc";
    }>({
        searchInput: "",
        alphabeticSort: null,
        confidenceSort: null,
    });
    const [currentSelectedSpecies, setCurrentSelectedSpecies] =
        useState<Species | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [uploadCredentialsSet, setUploadCredentialsSet] = useState(false);
    const [currentUploadStatus, setCurrentUploadStatus] = useState<"idle" | "downloadReady" | "success" | "error" | "forbidden">("idle");
    const [currentBirdweatherUploadStatus, setCurrentBirdweatherUploadStatus] = useState<"idle" | "downloadReady" | "success" | "error" | "forbidden">("idle");
    const [birdweatherCredentialsSet, setBirdweatherCredentialsSet] = useState(false);


    const filteredSpecies = species
        .filter(
            (s) =>
                s.commonName
                    .toLowerCase()
                    .includes(filter.searchInput.toLowerCase()) ||
                s.scientificName
                    .toLowerCase()
                    .includes(filter.searchInput.toLowerCase()),
        )
        .sort((a, b) => {
            if (filter.confidenceSort !== null) {
                const diff =
                    filter.confidenceSort === "asc"
                        ? a.avgConfidence - b.avgConfidence
                        : b.avgConfidence - a.avgConfidence;
                if (diff !== 0) return diff;
            }
            if (filter.alphabeticSort !== null) {
                const cmp = a.commonName.localeCompare(b.commonName);
                return filter.alphabeticSort === "asc" ? cmp : -cmp;
            }
            return 0;
        });

    const fetchSpecies = async () => {
        setIsLoading(true);

        const speciesList = await ListService.getBirdsList();
        setSpecies(speciesList);

        const urlCredential = await SettingsService.getSetting("supabaseUrl");
        const keyCredential = await SettingsService.getSetting("supabaseKey");
        const credentialsSet = urlCredential?.value !== undefined && urlCredential?.value !== "" && keyCredential?.value !== undefined && keyCredential?.value !== "";
        setUploadCredentialsSet(credentialsSet);
        if (!credentialsSet) {
            setCurrentUploadStatus("forbidden");
        } else if (speciesList.length === 0) {
            setCurrentUploadStatus("downloadReady");
        }

        const birdweatherCredential = await SettingsService.getSetting("birdWeatherToken");
        const birdweatherCredentialsSet = birdweatherCredential?.value !== undefined && birdweatherCredential?.value !== "";

        setBirdweatherCredentialsSet(birdweatherCredentialsSet);
        if (!birdweatherCredentialsSet) {
            setCurrentBirdweatherUploadStatus("forbidden");
        }

        setIsLoading(false);
    };

    const startUpload = async () => {
        console.log("Starting upload...");
        if (!uploadCredentialsSet) {
            return;
        }

        try {
            setIsLoading(true);
            if (species.length !== 0) {
                await CloudService.syncToSupabase();
            }

            await CloudService.fetchFromSupabase();

            await fetchSpecies();
            setCurrentUploadStatus("success");

        } catch (error) {
            console.error("Error syncing to cloud:", error);
            setCurrentUploadStatus("error");
        } finally {
            setTimeout(() => {
                setCurrentUploadStatus("idle");
            }, 2000);
        }
    }

    const startBirdweatherUpload = async () => {
        console.log("Starting birdweather upload...");
        if (!birdweatherCredentialsSet) {
            return;
        }

        try {
            setIsLoading(true);
            if (species.length !== 0) {
                await CloudService.syncToBirdWeather();
            }

            setIsLoading(false);

            setCurrentBirdweatherUploadStatus("success");

        } catch (error) {
            console.error("Error syncing to birdweather:", error);
            setCurrentBirdweatherUploadStatus("error");
        } finally {
            setTimeout(() => {
                setCurrentBirdweatherUploadStatus("idle");
            }, 2000);
        }
    }

    useEffect(() => {
        fetchSpecies();
    }, []);

    const styles = {
        speciesCardsWrapper: {
            marginTop: "20px",
            display: "flex",
            flexDirection: "column" as const,
            gap: "15px",
        },
        uploadButton: {
            "background": currentUploadStatus === "success" ? "green" : currentUploadStatus === "error" ? "red" : "var(--gradiant-clay)",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "position": "absolute" as const,
            "top": "-65px",
            "right": "7px",
            "color": "var(--cornsilk)",
            "padding": "12px",
            "borderRadius": "15px",
            "gap": "5px",
            "fontWeight": "600",
            "fontSize": "19px",
            "opacity": uploadCredentialsSet ? 1 : 0.5,
            "width": "120px",
            "zIndex": 10,
        },
        placeholder: {
            "marginTop": "20px",
            "opacity": "0.6"
        }
    };

    return (
        <div>
            <TabHeader
                tab="DETECTIONS"
                title="Your birds"
                subTitle={`${species.length} species · ${species.reduce((acc, s) => acc + s.detections, 0)} detections`}
            />

            <SyncButtons
                currentCloudUploadStatus={currentUploadStatus}
                startCloudUpload={startUpload}
                currentBirdWeatherUploadStatus={currentBirdweatherUploadStatus}
                startBirdWeatherUpload={startBirdweatherUpload}
            />

            <Filters filter={filter} setFilter={setFilter} />

            <div style={styles.speciesCardsWrapper}>
                {filteredSpecies && filteredSpecies.length > 0 ? (
                    filteredSpecies.map((specie, index) => (
                        <SpeciesListItem
                            key={specie.commonName}
                            species={specie}
                            onClick={() => {
                                setCurrentSelectedSpecies(specie);
                            }}
                        />
                    ))
                ) : (
                    <div style={styles.placeholder}>No detections synced yet</div>
                )}
            </div>

            <div>
                {currentSelectedSpecies && (
                    <SpeciesDetails
                        species={currentSelectedSpecies}
                        onClose={() => setCurrentSelectedSpecies(null)}
                    />
                )}
            </div>

            {isLoading && <LoadingSpinner />}
        </div>
    );
};

export default Birds;
