import { useEffect, useRef, useState } from "react";
import TabHeader from "../../components/TabHeader";
import { Wifi, Download, Check } from "lucide-react";
import SyncService from "../../lib/services/SyncService";
import { SYNC_ROW_LIMIT } from "../../lib/constants";
import DeviceService from "../../lib/services/DeviceService";

const Sync = () => {
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncProgress, setSyncProgress] = useState(0);
    const [temporaryStatusMessage, setTemporaryStatusMessage] = useState<
        string | null
    >(null);
    const [temporaryStatusType, setTemporaryStatusType] = useState<
        "info" | "success" | null
    >(null);
    const temporaryStatusTimeoutRef = useRef<ReturnType<
        typeof setTimeout
    > | null>(null);

    useEffect(() => {
        return () => {
            if (temporaryStatusTimeoutRef.current) {
                clearTimeout(temporaryStatusTimeoutRef.current);
            }
        };
    }, []);

    const showTemporaryStatusMessage = (
        message: string,
        duration = 2000,
        type: "info" | "success" = "info",
    ) => {
        setTemporaryStatusMessage(message);
        setTemporaryStatusType(type);

        if (temporaryStatusTimeoutRef.current) {
            clearTimeout(temporaryStatusTimeoutRef.current);
        }

        temporaryStatusTimeoutRef.current = setTimeout(() => {
            setTemporaryStatusMessage(null);
            setTemporaryStatusType(null);
            temporaryStatusTimeoutRef.current = null;
        }, duration);
    };

    const startSync = async () => {
        if (isSyncing) {
            return; // Prevent multiple sync operations
        }

        const deviceDetails = await DeviceService.getDeviceDetails();
        if (
            deviceDetails.ssid === "" ||
            deviceDetails.ssid === null ||
            deviceDetails.name === "Not connected"
        ) {
            showTemporaryStatusMessage(
                "Please connect to your device hotspot before syncing",
            );
            return;
        }

        try {
            const pendingAmount =
                await SyncService.getPendingDetectionsAmount();
            console.log("Pending detections amount:", pendingAmount);

            if (pendingAmount === false || pendingAmount === 0) {
                console.log("No pending detections to sync");
                showTemporaryStatusMessage("No pending detections to sync");
                setIsSyncing(false);
                return;
            }

            setIsSyncing(true);
            setSyncProgress(0);

            let offset = 0;
            let syncCompletedSuccessfully = true;
            while (offset < pendingAmount) {
                const syncSuccess = await SyncService.syncData(offset);
                if (!syncSuccess) {
                    console.error("Sync failed at offset:", offset);
                    syncCompletedSuccessfully = false;
                    break;
                }

                offset += SYNC_ROW_LIMIT;

                // Update progress based on offset and pendingAmount
                setSyncProgress(
                    Math.min(100, Math.round((offset / pendingAmount) * 100)),
                );

                console.log(
                    `Synced ${Math.min(offset, pendingAmount)} of ${pendingAmount} detections`,
                );
            }

            if (syncCompletedSuccessfully) {
                const deleteSuccess = await SyncService.deleteSyncedData();
                if (deleteSuccess) {
                    setSyncProgress(100);
                    showTemporaryStatusMessage(
                        "Sync completed successfully",
                        2000,
                        "success",
                    );
                }
            }
        } catch (error) {
            console.error("Sync error:", error);
        } finally {
            setIsSyncing(false);
        }
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
                !isSyncing || temporaryStatusMessage
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
                        ) : temporaryStatusType === "success" ? (
                            <Check size={75} aria-hidden="true" />
                        ) : (
                            <Wifi size={75} aria-hidden="true" />
                        )}
                    </div>
                </div>

                <div>
                    {temporaryStatusMessage ? (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div>{temporaryStatusMessage}</div>
                        </div>
                    ) : !isSyncing ? (
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
                    <div
                        onClick={startSync}
                        style={{
                            ...styles.startButton,
                            opacity: isSyncing ? 0.6 : 1,
                        }}
                    >
                        {isSyncing ? "Syncing..." : "Start Sync"}
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
