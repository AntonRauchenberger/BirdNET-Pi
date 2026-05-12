import { Species } from "../../../lib/types";
import { ChevronRight, Bird } from "lucide-react";

const SpeciesListItem = ({
    species,
    onClick,
}: {
    species: Species;
    onClick: () => void;
}) => {
    const styles = {
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
        <div style={styles.speciesCard} onClick={onClick}>
            <div style={styles.birdImnageContainer}>
                <Bird size={35} />
            </div>
            <div style={styles.speciesCardContentWrapper}>
                <div style={styles.speciesCardValueContainer}>
                    <div>
                        <div style={styles.speciesCommonName}>
                            {species.commonName}
                        </div>
                        <div style={styles.speciesScientificName}>
                            {species.scientificName}
                        </div>
                    </div>
                    <div style={styles.statusBarWrapper}>
                        <div style={styles.statusBarContainer}>
                            <div
                                style={{
                                    ...styles.statusBarValue,
                                    width: `${species.avgConfidence}%`,
                                }}
                            ></div>
                        </div>
                        <div
                            style={{
                                fontSize: "14px",
                                opacity: "0.7",
                            }}
                        >
                            {species.avgConfidence}%
                        </div>
                    </div>
                </div>
                <div style={{ transform: "translateX(10px)" }}>
                    <ChevronRight size={22} />
                </div>
            </div>
        </div>
    );
};

export default SpeciesListItem;
