import { useEffect, useRef, useState } from "react";
import TabHeader from "../../components/TabHeader";
import { Wifi, Download, Check } from "lucide-react";
import SyncService from "../../lib/services/SyncService";
import { SYNC_ROW_LIMIT } from "../../lib/constants";
import DeviceService from "../../lib/services/DeviceService";
import ListService from "../../lib/services/ListService";
import LoadingSpinner from "../../components/LoadingSpinner";
import CloudService from "../../lib/services/CloudService";

const Sync = () => {
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncProgress, setSyncProgress] = useState(0);
    const [temporaryStatusMessage, setTemporaryStatusMessage] = useState<
        string | null
    >(null);
    const [temporaryStatusType, setTemporaryStatusType] = useState<
        "info" | "success" | "error" | null
    >(null);
    const temporaryStatusTimeoutRef = useRef<ReturnType<
        typeof setTimeout
    > | null>(null);
    const [syncingInfo, setSyncingInfo] = useState("Transfering detections ...");
    const [isLoading, setIsLoading] = useState(false);

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
        type: "info" | "success" | "error" = "info",
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

    const syncDetections = async (pendingAmount: any) => {
        if (pendingAmount === false || pendingAmount === 0) {
            return true;
        }

        setIsSyncing(true);
        setSyncProgress(0);
        setSyncingInfo("Transfering detections ...");

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

        return syncCompletedSuccessfully;
    };

    const syncAudioFiles = async (pendingAmount: any) => {
        if (pendingAmount === false || pendingAmount === 0) {
            return true;
        }

        setIsSyncing(true);
        setSyncProgress(0);
        setSyncingInfo("Transfering audio files ...");

        const speciesList = await ListService.getBirdsList();
        const speciesToSync = speciesList.slice(0, pendingAmount);
        const totalSpeciesToSync = speciesToSync.length;

        let offset = 0;
        let syncCompletedSuccessfully = true;
        while (offset < totalSpeciesToSync) {
            const species = speciesToSync[offset];
            if (!species) {
                syncCompletedSuccessfully = false;
                break;
            }

            const syncSuccess = await SyncService.syncAudioFiles(
                species.commonName,
            );
            if (!syncSuccess) {
                console.error("Sync failed at offset:", offset);
                syncCompletedSuccessfully = false;
                break;
            }

            offset += 1;

            // Update progress based on offset and pendingAmount
            setSyncProgress(
                Math.min(100, Math.round((offset / totalSpeciesToSync) * 100)),
            );

            console.log(
                `Synced ${Math.min(offset, pendingAmount)} of ${pendingAmount} audio files`,
            );
        }

        return syncCompletedSuccessfully;
    }

    const startSync = async () => {
        if (isSyncing) {
            return; // Prevent multiple sync operations
        }

        setIsLoading(true);

        const deviceDetails = await DeviceService.getDeviceDetails();
        if (
            deviceDetails.ssid === "" ||
            deviceDetails.ssid === null ||
            deviceDetails.name === "Not connected"
        ) {
            setIsLoading(false);
            showTemporaryStatusMessage(
                "Please connect to your device hotspot before syncing",
                2000,
                "error",
            );
            return;
        }

        setIsLoading(false);

        try {
            const pendingAmounts = await SyncService.getPendingDetectionsAmount();
            if (pendingAmounts === false || (pendingAmounts.detectionsAmount === 0 && pendingAmounts.speciesAmount === 0)) {
                console.log("No pending data to sync");
                showTemporaryStatusMessage(
                    "No pending data to sync",
                    2000,
                    "info",
                );
                setIsSyncing(false);
                return;
            }

            console.log("Pending detections to sync:", pendingAmounts.detectionsAmount);
            console.log("Pending species to sync:", pendingAmounts.speciesAmount);

            const successfulDetectionsSync = await syncDetections(pendingAmounts.detectionsAmount);
            if (!successfulDetectionsSync) {
                throw new Error("Failed to sync detections");
            }

            const successfulAudioSync = await syncAudioFiles(pendingAmounts.speciesAmount);
            if (!successfulAudioSync) {
                throw new Error("Failed to sync audio files");
            }

            if (successfulDetectionsSync && successfulAudioSync) {
                await SyncService.deleteSyncedData();
            }

            // Sync data to cloud if credentials are available
            await CloudService.syncToSupabase();

            setSyncProgress(100);
            showTemporaryStatusMessage(
                "Sync completed successfully",
                2000,
                "success",
            );
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
                temporaryStatusType === "error"
                    ? "red"
                    : temporaryStatusType === "info"
                        ? "blue"
                        : !isSyncing || temporaryStatusMessage
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
            marginTop: "50%",
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
            top: "55.5%",
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
        statusPositonWrapper: {
            position: "absolute" as const,
            top: "49%",
            width: "85%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
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

                <div style={styles.statusPositonWrapper}>
                    {temporaryStatusMessage ? (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div style={{ maxWidth: "90%" }}>
                                {temporaryStatusMessage}
                            </div>
                        </div>
                    ) : !isSyncing ? (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div style={{ maxWidth: "90%" }}>Ready to sync</div>
                        </div>
                    ) : isSyncing ? (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div style={{ maxWidth: "90%" }}>Synching ...</div>
                        </div>
                    ) : (
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div style={{ maxWidth: "90%" }}>
                                Connect to your device hotspot
                            </div>
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
                            <div>{syncingInfo}</div>
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
            {isLoading && <LoadingSpinner />}
        </div>
    );
};

export default Sync;
