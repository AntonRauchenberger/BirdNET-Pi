import { Species } from "../../lib/types";
import { X, Bird, MapPin, Calendar, Volume2, ChevronRight, Pause } from "lucide-react";
import { useEffect, useState } from "react";

import LocationMap from "./LocationMap";
import ListService from "../../lib/services/ListService";

export const SpeciesDetails = (props: {
    species: Species;
    onClose: () => void;
}) => {
    const [isClosing, setIsClosing] = useState(false);
    const [showLocationMap, setShowLocationMap] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [isAudioPlaying, setIsAudioPlaying] = useState(false);

    useEffect(() => {
        return () => {
            if (audioUrl) {
                URL.revokeObjectURL(audioUrl);
            }
        };
    }, [audioUrl]);

    const handleClose = () => {
        setIsClosing(true);
        setTimeout(() => {
            props.onClose();
        }, 300);
    };

    const getTimeAgo = (date: any) => {
        const diffMs = Date.now() - new Date(date).getTime();

        const minutes = Math.floor(diffMs / 1000 / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (minutes < 60) {
            return `${minutes} min ago`;
        }

        if (hours < 24) {
            return `${hours} h ago`;
        }

        return `${days} days ago`;
    };

    const playAudio = async () => {
        const audioBlob = await ListService.getSpeciesAudioBlob(props.species);

        if (audioBlob) {
            if (audioUrl) {
                URL.revokeObjectURL(audioUrl);
            }

            const url = URL.createObjectURL(audioBlob);
            setAudioUrl(url);
            setIsAudioPlaying(true);
        }
    };

    const keyframes = `
        @keyframes slideUp {
            from {
                transform: translateY(100%);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
            }
            to {
                opacity: 1;
            }
        }
    `;

    const styles = {
        keyframeStyle: {
            animation: keyframes,
        } as any,
        anchorWrapper: {
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "5px",
            marginBottom: "10px",
        },
        anchorBar: {
            width: "50px",
            height: "100%",
            background: "var(--seccondary)",
            borderRadius: "10px",
        },
        backgroundBlur: {
            width: "100%",
            height: "100%",
            position: "fixed" as const,
            top: "0",
            left: "0",
            zIndex: "11",
            background: "color-mix(in oklab, var(--forest) 40%, transparent)",
            animation: isClosing
                ? "fadeOut 0.3s ease-out forwards"
                : "fadeIn 0.3s ease-out forwards",
        },
        card: {
            background: "var(--card)",
            borderRadius: "1.5rem 1.5rem 0 0",
            border: props.species.uncommon ? "5px solid var(--sunlit-clay)" : "var(--card-border)",
            boxShadow: "var(--shadow-soft)",
            position: "fixed" as const,
            bottom: "45px",
            zIndex: "12",
            width: "89%",
            maxWidth: "var(--iphone-max-width)",
            transform: "translateX(-50%)",
            padding: props.species.uncommon ? "1rem" : "1.25rem",
            maxHeight: "90vh",
            overflowY: "auto" as const,
            animation: isClosing
                ? "slideDown 0.3s ease-out forwards"
                : "slideUp 0.4s ease-out forwards",
            left: "20px",
            right: "20px",
        },
        headingWrapper: {
            display: "flex",
            justifyContent: "space-between",
        },
        headingsContainer: {
            textAlign: "left" as const,
            display: "flex",
            flexDirection: "column" as const,
            gap: "2px",
        },
        info: {
            fontWeight: "500",
            fontSize: "15px",
        },
        comName: {
            fontSize: "24px",
            fontWeight: "600",
            color: "black",
        },
        scientificName: {
            fontStyle: "italic",
            opacity: "0.8",
        },
        xButtone: {
            height: "40px",
            width: "40px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            background: "var(--gradiant-clay)",
            borderRadius: "50%",
            color: "var(--card)",
            border: "none",
            cursor: "pointer",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
        },
        xButtonHover: {
            transform: "scale(1.05)",
            boxShadow: "0 4px 12px rgba(221, 161, 94, 0.3)",
        },
        birdImageContainer: {
            marginTop: "15px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            background: "var(--gradiant-leaf)",
            color: "var(--card)",
            height: "190px",
            borderRadius: "1.5rem",
            overflow: "hidden",
        },
        infoCardsWrapper: {
            display: "flex",
            justifyContent: "space-between",
            gap: "10px",
            alignItems: "center",
            marginTop: "15px",
        },
        infoCard: {
            background: "var(--cornsilk)",
            padding: "10px 2px",
            borderRadius: "1rem",
            width: "33%",
            display: "flex",
            flexDirection: "column" as const,
            alignItems: "center",
            border: "var(--card-border)",
        },
        infoCardHeading: {
            fontSize: "10px",
            fontWeight: "600",
            opacity: "0.6",
        },
        infoCardValue: {
            fontSize: "17px",
            fontWeight: "500",
        },
        infoListWrapper: {
            display: "flex",
            flexDirection: "column" as const,
            gap: "8px",
            marginTop: "15px",
        },
        infoListItem: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            border: "var(--card-border)",
            padding: "10px 11px 5px 11px",
            borderRadius: "2rem",
        },
        infoListItemHover: {
            background: "color-mix(in oklab, var(--cornsilk) 40%, transparent)",
        },
        infoListHeadingWrapper: {
            display: "flex",
            gap: "5px",
        },
        infoListHeading: {
            fontSize: "14px",
            opacity: "0.75",
        },
        infoListIcon: {
            opacity: "0.75",
        },
        infoListValue: {
            fontSize: "15px",
            fontWeight: "500",
        },
        playButton: {
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: "8px",
            background: "var(--gradiant-clay)",
            color: "var(--card)",
            borderRadius: "30px",
            height: "50px",
            fontWeight: "600",
            marginTop: "15px",
            marginBottom: "25px",
            border: "none",
            cursor: "pointer",
            transition: "transform 0.2s ease",
            width: "100%",
            fontSize: "16px",
        },
        playButtonHover: {
            transform: "translateY(-2px)",
        },
        playButtonIcon: {
            transform: "translateY(2px)",
        },
        locationValueWrapper: {
            display: "flex",
            gap: "3px",
            alignItems: "center",
        },
        rareBadge: {
            "position": "absolute" as const,
            "transform": "translate3d(89px, 13px, 0px)",
            "background": "var(--gradiant-clay)",
            "padding": "1px 10px",
            "color": "var(--card)",
            "fontSize": "12px",
            "fontWeight": "600",
            "borderRadius": "20px"
        }
    };

    return (
        <>
            <style>{`
                @keyframes slideUp {
                    from {
                        transform: translateY(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }

                @keyframes slideDown {
                    from {
                        transform: translateY(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateY(100%);
                        opacity: 0;
                    }
                }

                @keyframes fadeIn {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                }

                @keyframes fadeOut {
                    from {
                        opacity: 1;
                    }
                    to {
                        opacity: 0;
                    }
                }
            `}</style>
            <div style={styles.backgroundBlur} onClick={handleClose}></div>
            <div style={styles.card}>
                {props.species.uncommon && (
                    <div style={{ position: "relative" }}>
                        <div style={styles.rareBadge}>UNCOMMON</div>
                    </div>
                )}
                <div style={styles.anchorWrapper}>
                    <div style={styles.anchorBar}></div>
                </div>
                <div style={styles.headingWrapper}>
                    <div style={styles.headingsContainer}>
                        <div style={styles.info}>DETECTION</div>
                        <div style={styles.comName}>
                            {props.species.commonName}
                        </div>
                        <div style={styles.scientificName}>
                            {props.species.scientificName}
                        </div>
                    </div>
                    <button
                        style={styles.xButtone}
                        onClick={handleClose}
                        onMouseEnter={(e) => {
                            Object.assign(
                                e.currentTarget.style,
                                styles.xButtonHover,
                            );
                        }}
                        onMouseLeave={(e) => {
                            Object.assign(e.currentTarget.style, {
                                transform: "",
                                boxShadow: "",
                            });
                        }}
                    >
                        <X size={20} />
                    </button>
                </div>

                <div style={styles.birdImageContainer}>
                    {props.species.imageUrl && props.species.imageUrl !== "" ? (
                        <img
                            src={props.species.imageUrl}
                            alt={props.species.commonName}
                            style={{
                                width: "100%",
                                height: "100%",
                                objectFit: "cover" as const,
                                display: "block",
                            }}
                        />
                    ) : (
                        <Bird size={48} />
                    )}
                </div>

                <div style={styles.infoCardsWrapper}>
                    <div style={styles.infoCard}>
                        <div style={styles.infoCardHeading}>CONFIDENCE</div>
                        <div style={styles.infoCardValue}>
                            {props.species.avgConfidence}%
                        </div>
                    </div>

                    <div style={styles.infoCard}>
                        <div style={styles.infoCardHeading}>DETECTIONS</div>
                        <div style={styles.infoCardValue}>
                            {props.species.detections}
                        </div>
                    </div>

                    <div style={styles.infoCard}>
                        <div style={styles.infoCardHeading}>LAST CALL</div>
                        <div
                            style={{
                                ...styles.infoCardValue,
                                fontSize: "15px",
                            }}
                        >
                            {getTimeAgo(props.species.lastCall)}
                        </div>
                    </div>
                </div>

                <div style={styles.infoListWrapper}>
                    <div
                        style={styles.infoListItem}
                        onClick={() => setShowLocationMap(true)}
                        onMouseEnter={(e) => {
                            Object.assign(
                                e.currentTarget.style,
                                styles.infoListItemHover,
                            );
                        }}
                        onMouseLeave={(e) => {
                            Object.assign(e.currentTarget.style, {
                                background: "",
                            });
                        }}
                    >
                        <div style={styles.infoListHeadingWrapper}>
                            <div style={styles.infoListIcon}>
                                <MapPin size={18} />
                            </div>
                            <div style={styles.infoListHeading}>
                                Last location
                            </div>
                        </div>
                        <div style={styles.locationValueWrapper}>
                            <div style={styles.infoListValue}>
                                {props.species.latitude.toFixed(4)},{" "}
                                {props.species.longitude.toFixed(4)}
                            </div>
                            <ChevronRight
                                size={20}
                                style={{ transform: "translateY(-1px)" }}
                            />
                        </div>
                    </div>

                    <div style={styles.infoListItem}>
                        <div style={styles.infoListHeadingWrapper}>
                            <div style={styles.infoListIcon}>
                                <Calendar size={20} />
                            </div>
                            <div style={styles.infoListHeading}>First seen</div>
                        </div>
                        <div style={styles.infoListValue}>
                            {new Date(props.species.firstSeen).toLocaleString()}
                        </div>
                    </div>
                </div>

                <button style={styles.playButton} onClick={() => {
                    if (isAudioPlaying) {
                        setAudioUrl(null);
                        setIsAudioPlaying(false);
                    } else {
                        playAudio();
                    }
                }}>
                    {isAudioPlaying ? (
                        <><div style={styles.playButtonIcon}>
                            <Pause size={18} />
                        </div><div>Stop audio</div></>
                    ) : (
                        <><div style={styles.playButtonIcon}>
                            <Volume2 size={18} />
                        </div><div>Play last recording</div></>
                    )}
                </button>
                {showLocationMap && (
                    <LocationMap
                        latitude={props.species.latitude}
                        longitude={props.species.longitude}
                        commonName={props.species.commonName}
                        onClose={() => setShowLocationMap(false)}
                    />
                )}
                {audioUrl && (
                    <audio
                        src={audioUrl}
                        controls
                        autoPlay
                        style={{ display: "none" }}
                        onEnded={() => {
                            setAudioUrl(null);
                            setIsAudioPlaying(false);
                        }}
                    />
                )}
            </div>
        </>
    );
};

export default SpeciesDetails;
