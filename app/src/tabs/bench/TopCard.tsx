import { Play, CircleX, Check, Ban } from "lucide-react";
import { useEffect, useState } from "react";
import { DeviceDetails } from "../../lib/types";

const TopCard = (props: {
    deviceInfo: DeviceDetails | null;
    startBenchmarking: () => void;
    currentState: "inactive" | "processing" | "error" | "success";
}) => {
    const [showProcessingIcon, setShowProcessingIcon] = useState(true);

    useEffect(() => {
        if (props.currentState !== "processing") {
            setShowProcessingIcon(true);
            return;
        }

        const interval = setInterval(() => {
            setShowProcessingIcon((prev) => !prev);
        }, 500);

        return () => clearInterval(interval);
    }, [props.currentState]);

    const styles = {
        topCard: {
            "background": "var(--gradiant-leaf)",
            "padding": "1rem 1.25rem 1.25rem",
            "borderRadius": "1.5rem",
            "boxShadow": "var(--shadow-soft)",
            "display": "flex",
            "flexDirection": "column" as const,
            "color": "var(--cornsilk)"
        },
        startButton: {
            "display": "flex",
            "width": "100%",
            "justifyContent": "center",
            "alignItems": "center",
            "background": "var(--gradiant-clay)",
            "color": "var(--card)",
            "gap": "5px",
            "padding": "10px",
            "borderRadius": "15px",
            "textDecoration": "none",
        },
        startButtonText: {
            "color": "var(--card)",
            "fontSize": "18px",
            "fontWeight": "600"
        },
        subCardsWrapper: {
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "marginTop": "20px",
            "gap": "20px"
        },
        subCard: {
            "display": "flex",
            "flexDirection": "column" as const,
            "alignItems": "center",
            "backgroundColor": "color-mix(in oklab, var(--cornsilk) 15%, transparent)",
            "borderRadius": "18px",
            "padding": "10px",
            "width": "50%"
        },
        subCardTitle: {
            "letterSpacing": "1px",
            "fontWeight": "600",
            "textAlign": "left" as const,
            "fontSize": "13px",
            "opacity": "0.7"
        },
        subCardValue: {
            "fontWeight": "600",
            "textAlign": "left" as const,
            "fontSize": "18px"
        }
    }

    return (
        <div style={styles.topCard}>
            {props.currentState === "inactive" ? (
                <div style={styles.startButton} onClick={props.startBenchmarking}>
                    <div style={{ transform: "translateY(3px)" }}>
                        {props.deviceInfo && props.deviceInfo.name && props.deviceInfo.name !== "Not connected" ? (
                            <Play size={20} aria-hidden="true" />
                        ) : (
                            <Ban size={20} aria-hidden="true" />
                        )}
                    </div>
                    <div style={styles.startButtonText}>
                        Start Benchmark
                    </div>
                </div>
            ) : props.currentState === "error" ? (
                <div style={{ ...styles.startButton, background: "red" }}>
                    <div style={{ transform: "translateY(3px)" }}>
                        <CircleX size={20} aria-hidden="true" />
                    </div>
                    <div style={styles.startButtonText}>
                        Error starting benchmark
                    </div>
                </div>
            ) : props.currentState === "success" ? (
                <div style={{ ...styles.startButton, background: "green" }}>
                    <div style={{ transform: "translateY(3px)" }}>
                        <Check size={20} aria-hidden="true" />
                    </div>
                    <div style={styles.startButtonText}>
                        Started successfully
                    </div>
                </div>
            ) : props.currentState === "processing" ? (
                <div style={styles.startButton}>
                    <div style={{ transform: "translateY(3px)", opacity: showProcessingIcon ? 1 : 0.2, transition: "opacity 0.2s ease" }}>
                        <Play size={20} aria-hidden="true" />
                    </div>
                    <div style={styles.startButtonText}>
                        Benchmarking in progress ...
                    </div>
                </div>
            ) : null}

            <div style={styles.subCardsWrapper}>
                <div style={styles.subCard}>
                    <div style={styles.subCardTitle}>
                        DEVICE
                    </div>
                    <div style={styles.subCardValue}>
                        {props?.deviceInfo?.name || "Not connected"}
                    </div>
                </div>

                <div style={styles.subCard}>
                    <div style={styles.subCardTitle}>
                        STORAGE
                    </div>
                    <div style={styles.subCardValue}>
                        {props?.deviceInfo?.storage || 0} %
                    </div>
                </div>
            </div>
        </div>
    )
}

export default TopCard;