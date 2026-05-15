import { useEffect, useState } from "react";
import TabHeader from "../../components/TabHeader";
import { Species } from "../../lib/types";
import Filters from "./Filters";
import SpeciesListItem from "./SpeciesListItem";
import SpeciesDetails from "./SpeciesDetails";
import ListService from "../../lib/services/ListService";

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
        // TODO add loading state
        const speciesList = await ListService.getBirdsList();
        setSpecies(speciesList);
    };

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
                            setCurrentSelectedSpecies(specie);
                        }}
                    />
                ))}
            </div>

            <div>
                {currentSelectedSpecies && (
                    <SpeciesDetails
                        species={currentSelectedSpecies}
                        onClose={() => setCurrentSelectedSpecies(null)}
                    />
                )}
            </div>
        </div>
    );
};

export default Birds;
