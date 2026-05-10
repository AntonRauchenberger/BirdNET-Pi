import { useState } from "react";
import TabHeader from "../../components/TabHeader";
import { Species } from "../../../lib/types";
import Filters from "./Filters";
import SpeciesListItem from "./SpeciesListItem";

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
                    <SpeciesListItem
                        key={specie.commonName}
                        species={specie}
                        onClick={() => {
                            console.log("TODO");
                        }}
                    />
                ))}
            </div>
        </div>
    );
};

export default Birds;
