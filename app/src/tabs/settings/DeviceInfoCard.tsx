import { HardDrive } from "lucide-react";
import { DeviceInfo } from "../../lib/types";

const DeviceInfoCard = ({ deviceInfo }: { deviceInfo: DeviceInfo }) => {
    const styles = {
        deviceCard: {
            background: "var(--gradiant-leaf)",
            borderRadius: "1.5rem",
            color: "var(--cornsilk)",
            marginTop: "30px",
            overflow: "hidden",
            padding: "1.25rem",
            boxShadow: "var(--shadow-soft)",
        },
        deviceNameWrapper: {
            display: "flex",
            gap: "10px",
            alignItems: "center",
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
    };

    return (
        <div style={styles.deviceCard}>
            <div style={styles.deviceNameWrapper}>
                <div style={styles.deviceIcon}>
                    <HardDrive size={20} aria-hidden="true" />
                </div>
                <div>
                    <div style={styles.subHeading}>PAIRED DEVICE</div>
                    <div style={styles.cardValue}>{deviceInfo.name}</div>
                </div>
            </div>

            <div style={styles.detailedValueWrapper}>
                <div style={styles.detailedValueCard}>
                    <div style={{ ...styles.subHeading, fontSize: "13px" }}>
                        BATTERY
                    </div>
                    <div style={styles.cardValue}>{deviceInfo.battery}%</div>
                </div>

                <div style={styles.detailedValueCard}>
                    <div style={{ ...styles.subHeading, fontSize: "13px" }}>
                        STORAGE
                    </div>
                    <div style={styles.cardValue}>{deviceInfo.storage}%</div>
                </div>

                <div style={styles.detailedValueCard}>
                    <div style={{ ...styles.subHeading, fontSize: "13px" }}>
                        UPTIME
                    </div>
                    <div style={styles.cardValue}>{deviceInfo.uptime}d</div>
                </div>
            </div>
        </div>
    );
};

export default DeviceInfoCard;
