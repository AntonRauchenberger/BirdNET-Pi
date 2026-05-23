import { HardDrive, RotateCw } from "lucide-react";
import { DeviceDetails } from "../../lib/types";

const DeviceInfoCard = (props: {
    deviceInfo: DeviceDetails;
    loadSettings: () => void;
    activeSubPage: string | null;
}) => {
    const styles = {
        deviceCard: {
            background: "var(--gradiant-leaf)",
            borderRadius: "1.5rem",
            color: "var(--cornsilk)",
            marginTop: "30px",
            overflow: "hidden",
            padding: "1.25rem",
            boxShadow: props.activeSubPage === null ? "var(--shadow-soft)" : "none"
        },
        deviceNameWrapper: {
            display: "flex",
            gap: "10px",
            alignItems: "center",
            justifyContent: "space-between",
        },
        deviceNameContainer: {
            display: "flex",
            alignItems: "center",
            gap: "10px",
        },
        deviceIcon: {
            backgroundColor:
                "color-mix(in oklab, var(--cornsilk) 15%, transparent)",
            height: "55px",
            width: "55px",
            borderRadius: "50%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
        },
        subHeading: {
            color: "color-mix(in oklab, var(--cornsilk) 70%, transparent)",
            letterSpacing: "1px",
            fontWeight: "600",
            textAlign: "left" as const,
            fontSize: "15px",
        },
        cardValue: {
            fontWeight: "600",
            textAlign: "left" as const,
            fontSize: "19px",
        },
        detailedValueWrapper: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "20px",
        },
        detailedValueCard: {
            display: "flex",
            flexDirection: "column" as const,
            alignItems: "center",
            backgroundColor:
                "color-mix(in oklab, var(--cornsilk) 15%, transparent)",
            borderRadius: "18px",
            padding: "10px",
            width: "30%",
        },
        refreshButton: {
            background: "var(--gradiant-clay)",
            borderRadius: "50%",
            height: "40px",
            width: "40px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
        },
    };

    return (
        <div style={styles.deviceCard}>
            <div style={styles.deviceNameWrapper}>
                <div style={styles.deviceNameContainer}>
                    <div style={styles.deviceIcon}>
                        <HardDrive size={20} aria-hidden="true" />
                    </div>
                    <div>
                        <div style={styles.subHeading}>PAIRED DEVICE</div>
                        <div style={styles.cardValue}>
                            {props.deviceInfo.name}
                        </div>
                    </div>
                </div>
                <div style={styles.refreshButton} onClick={props.loadSettings}>
                    <RotateCw
                        size={20}
                        aria-hidden="true"
                        style={{ color: "var(--cornsilk)" }}
                    />
                </div>
            </div>

            <div style={styles.detailedValueWrapper}>
                <div style={styles.detailedValueCard}>
                    <div style={{ ...styles.subHeading, fontSize: "13px" }}>
                        BATTERY
                    </div>
                    <div style={styles.cardValue}>
                        {props.deviceInfo.battery}%
                    </div>
                </div>

                <div style={styles.detailedValueCard}>
                    <div style={{ ...styles.subHeading, fontSize: "13px" }}>
                        STORAGE
                    </div>
                    <div style={styles.cardValue}>
                        {props.deviceInfo.storage}%
                    </div>
                </div>

                <div style={styles.detailedValueCard}>
                    <div style={{ ...styles.subHeading, fontSize: "13px" }}>
                        UPTIME
                    </div>
                    <div style={styles.cardValue}>
                        {props.deviceInfo.uptime}d
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeviceInfoCard;
