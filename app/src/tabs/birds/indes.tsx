import { useState } from "react";
import TabHeader from "../../components/TabHeader";
import { Species } from "../../../lib/types";
import Filters from "./Filters";
import { ChevronRight, Bird } from "lucide-react";

const Birds = () => {
    const [species, setSpecies] = useState<Species[]>([
        {
            commonName: "European Robin",
            scientificName: "Erithacus rubecula",
            avgConfidence: 85,
            detections: 10,
            lastCall: Date.now() - 3600000,
            latitude: 52.52,
            longitude: 13.405,
            firstSeen: Date.now() - 7200000,
        },
        {
            commonName: "Great Tit",
            scientificName: "Parus major",
            avgConfidence: 78,
            detections: 5,
            lastCall: Date.now() - 1800000,
            latitude: 52.52,
            longitude: 13.405,
            firstSeen: Date.now() - 3600000,
        },
        {
            commonName: "Blackbird",
            scientificName: "Turdus merula",
            avgConfidence: 90,
            detections: 8,
            lastCall: Date.now() - 5400000,
            latitude: 52.52,
            longitude: 13.405,
            firstSeen: Date.now() - 10800000,
        },
    ]);
    const [filter, setFilter] = useState<{
        searchInput: string;
        alphabeticSort: null | "asc" | "desc";
        confidenceSort: null | "asc" | "desc";
    }>({
        searchInput: "",
        alphabeticSort: null,
        confidenceSort: null,
    });

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

    const styles = {
        speciesCardsWrapper: {
            marginTop: "20px",
            display: "flex",
            flexDirection: "column" as const,
            gap: "15px",
        },
        speciesCard: {
            display: "flex",
            alignItems: "center",
            background: "var(--card)",
            borderRadius: "1.5rem",
            padding: "0.7rem",
            boxShadow: "var(--shadow-soft)",
            border: "var(--card-border)",
            gap: "10px",
        },
        birdImnageContainer: {
            width: "55px",
            height: "55px",
            background: "var(--copper)",
            backgroundColor:
                "color-mix(in oklab, var(--copper) 15%, transparent)",
            borderRadius: "20px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
        },
        speciesCardContentWrapper: {
            display: "flex",
            width: "75%",
            alignItems: "center",
            justifyContent: "space-between",
        },
        speciesCardValueContainer: {
            textAlign: "left" as const,
            width: "90%",
        },
        speciesCommonName: {
            fontWeight: "600",
            fontSize: "18px",
        },
        speciesScientificName: {
            fontSize: "14px",
            opacity: "0.7",
            fontStyle: "oblique",
        },
        statusBarWrapper: {
            display: "flex",
            width: "100%",
            alignItems: "center",
            gap: "5px",
            marginTop: "-2px",
        },
        statusBarContainer: {
            width: "100%",
            background: "var(--cornsilk)",
            height: "7px",
            borderRadius: "30px",
        },
        statusBarValue: {
            height: "100%",
            width: "97%",
            background: "var(--gradiant-clay)",
            borderRadius: "30px",
        },
    };

    return (
        <div>
            <TabHeader
                tab="DETECTIONS"
                title="Your birds"
                subTitle={`${species.length} species · ${species.reduce((acc, s) => acc + s.detections, 0)} detections`}
            />
            <Filters filter={filter} setFilter={setFilter} />

            <div style={styles.speciesCardsWrapper}>
                {filteredSpecies.map((specie, index) => (
                    <div style={styles.speciesCard} key={index}>
                        <div style={styles.birdImnageContainer}>
                            <Bird size={35} />
                        </div>
                        <div style={styles.speciesCardContentWrapper}>
                            <div style={styles.speciesCardValueContainer}>
                                <div>
                                    <div style={styles.speciesCommonName}>
                                        {specie.commonName}
                                    </div>
                                    <div style={styles.speciesScientificName}>
                                        {specie.scientificName}
                                    </div>
                                </div>
                                <div style={styles.statusBarWrapper}>
                                    <div style={styles.statusBarContainer}>
                                        <div
                                            style={{
                                                ...styles.statusBarValue,
                                                width: `${specie.avgConfidence}%`,
                                            }}
                                        ></div>
                                    </div>
                                    <div
                                        style={{
                                            fontSize: "14px",
                                            opacity: "0.7",
                                        }}
                                    >
                                        {specie.avgConfidence}%
                                    </div>
                                </div>
                            </div>
                            <div style={{ transform: "translateX(10px)" }}>
                                <ChevronRight size={22} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Birds;
