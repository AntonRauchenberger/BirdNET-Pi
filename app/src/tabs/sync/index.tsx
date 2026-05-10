import { useState } from "react";
import TabHeader from "../../components/TabHeader";
import { Wifi, Download } from "lucide-react";

const Sync = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncProgress, setSyncProgress] = useState(0);

    const startSync = () => {
        if (!isConnected) {
            // TODO remove comment
            // return;
        }

        setIsConnected(true);
        setIsSyncing(true);
        // Simulate sync progress
        const interval = setInterval(() => {
            setSyncProgress((prev) => {
                if (prev >= 100) {
                    clearInterval(interval);
                    setIsSyncing(false);
                    setIsConnected(false);
                    return 0;
                }
                return prev + 10;
            });
        }, 500);
    };

    const styles = {
        contentWrapper: {
            display: "flex",
            flexDirection: "column" as const,
            alignItems: "center",
            marginTop: "90px",
        },
        outerCircle: {
            background: "var(--gradiant-leaf)",
            width: "200px",
            height: "200px",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
        },
        innerCircle: {
            background: "var(--card)",
            borderRadius: "50%",
            width: "150px",
            height: "150px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
        },
        statusWrapper: {
            display: "flex",
            alignItems: "center",
            gap: "7px",
            marginTop: "30px",
        },
        statusIcon: {
            background:
                isConnected && !isSyncing
                    ? "green"
                    : isSyncing
                      ? "orange"
                      : "red",
            width: "13px",
            height: "13px",
            borderRadius: "50%",
            animation: isSyncing
                ? "sync-status-blink 1s ease-in-out infinite"
                : "none",
        },
        startButton: {
            background: "var(--gradiant-leaf)",
            width: "330px",
            height: "50px",
            color: "white",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            borderRadius: "35px",
            marginTop: "35%",
            fontSize: "15px",
            fontWeight: "500",
            opacity: isConnected ? 1 : 0.6,
        },
        infoCard: {
            background: "var(--card)",
            padding: "13px",
            borderRadius: "20px",
            textAlign: "left" as const,
            fontSize: "12px",
            marginTop: "20px",
            border: "var(--card-border)",
            width: "330px",
        },
        syncStatusWrapper: {
            background: "var(--card)",
            padding: "13px",
            borderRadius: "20px",
            textAlign: "left" as const,
            fontSize: "12px",
            marginTop: "20px",
            border: "var(--card-border)",
            width: "330px",
            position: "absolute" as const,
            top: "437px",
        },
        syncStatusBarContainer: {
            width: "100%",
            background: "var(--cornsilk)",
            height: "10px",
            borderRadius: "30px",
        },
        syncStatusBarValue: {
            height: "100%",
            width: `${syncProgress}%`,
            borderRadius: "30px",
            background: "var(--gradiant-clay)",
            transition: "width 0.5s ease-in-out",
        },
    };

    return (
        <div>
            <TabHeader
                tab={"SYNC"}
                title={"Pull fresh chirps"}
                subTitle={"Get the latest detections from your device."}
            />
            <div style={styles.contentWrapper}>
                <div style={styles.outerCircle}>
                    <div style={styles.innerCircle}>
                        {isSyncing ? (
                            <Download size={75} aria-hidden="true" />
                        ) : (
                            <Wifi size={75} aria-hidden="true" />
                        )}
                    </div>
                </div>

                <div>
                    {isConnected && !isSyncing ? (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div>Ready to sync</div>
                        </div>
                    ) : isSyncing ? (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div>Synching ...</div>
                        </div>
                    ) : (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div>Connect to your device hotspot</div>
                        </div>
                    )}
                </div>

                {isSyncing && (
                    <div style={styles.syncStatusWrapper}>
                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                            }}
                        >
                            <div>Transfer</div>
                            <div>{syncProgress}%</div>
                        </div>
                        <div style={styles.syncStatusBarContainer}>
                            <div style={styles.syncStatusBarValue}></div>
                        </div>
                    </div>
                )}

                <div>
                    <div style={styles.startButton} onClick={startSync}>
                        Start Sync
                    </div>
                </div>

                <div style={styles.infoCard}>
                    <span style={{ opacity: 0.6 }}>
                        Make sure the sync mode is enabled on your device and
                        that you are connected to its hotspot.
                    </span>
                </div>
            </div>
        </div>
    );
};

export default Sync;
