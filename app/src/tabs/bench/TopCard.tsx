import { Play } from "lucide-react";
import { DeviceDetails } from "../../lib/types";

const TopCard = (props: {
    deviceInfo: DeviceDetails | null;
    startBenchmarking: () => void;
}) => {

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
            "opacity": props?.deviceInfo?.name && props?.deviceInfo?.name !== "Not connected" ? 1 : 0.6,
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
            <div style={styles.startButton} onClick={props.startBenchmarking}>
                <div style={{ transform: "translateY(3px)" }}>
                    <Play size={20} aria-hidden="true" />
                </div>
                <div style={styles.startButtonText}>
                    Start Benchmark
                </div>
            </div>

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