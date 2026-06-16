import { useEffect, useRef, useState } from "react";
import TabHeader from "../../components/TabHeader";
import {
    Wifi,
    Download,
    Check,
    WifiSync,
    ShieldCheck,
    Radio,
} from "lucide-react";
import SyncService from "../../lib/services/SyncService";
import { SYNC_ROW_LIMIT } from "../../lib/constants";
import DeviceService from "../../lib/services/DeviceService";
import ListService from "../../lib/services/ListService";
import LoadingSpinner from "../../components/LoadingSpinner";

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
    const [syncingInfo, setSyncingInfo] = useState("Transferring detections ...");
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
        setSyncingInfo("Transferring detections ...");

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
        setSyncingInfo("Transferring audio files ...");

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
                "Please connect to your device hotspot",
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
                const deletedSyncedData = await SyncService.deleteSyncedData();
                if (!deletedSyncedData) {
                    throw new Error("Failed to delete synced data on device");
                }
            }

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
            setSyncProgress(0);
        }
    };

    const currentStatusText = temporaryStatusMessage
        ? temporaryStatusMessage
        : isSyncing
            ? "Syncing in progress"
            : "Ready to sync";

    const currentStatusColor =
        temporaryStatusType === "error"
            ? "red"
            : temporaryStatusType === "info"
                ? "var(--sunlit-clay)"
                : temporaryStatusType === "success"
                    ? "green"
                    : isSyncing
                        ? "var(--sunlit-clay)"
                        : "green";

    const currentSyncStep = isSyncing
        ? syncingInfo.toLowerCase().includes("audio")
            ? 2
            : 1
        : temporaryStatusType === "success"
            ? 3
            : 0;

    const syncSteps = [
        {
            title: "Connect",
            description: "Device hotspot",
            active: currentSyncStep >= 0,
            completed: currentSyncStep > 0,
            icon: Wifi,
        },
        {
            title: "Detections",
            description: "Transfer sightings",
            active: currentSyncStep === 1,
            completed: currentSyncStep > 1,
            icon: Download,
        },
        {
            title: "Audio",
            description: "Transfer audios",
            active: currentSyncStep === 2,
            completed: currentSyncStep > 2,
            icon: Radio,
        },
    ];

    const progressPanelText =
        temporaryStatusType === "success"
            ? "Sync complete"
            : temporaryStatusType === "error"
                ? "Sync interrupted"
                : isSyncing
                    ? syncingInfo
                    : "Waiting to start";

    const styles = {
        contentWrapper: {
            display: "flex",
            flexDirection: "column" as const,
            alignItems: "center",
            marginTop: "25px",
            width: "100%",
            maxWidth: "360px",
            marginInline: "auto",
            paddingInline: "2px",
            gap: "14px",
        },
        heroCard: {
            width: "100%",
            borderRadius: "28px",
            background: "var(--gradiant-leaf)",
            boxShadow: "var(--shadow)",
            padding: "22px 18px 16px",
            display: "flex",
            flexDirection: "column" as const,
            alignItems: "center",
            gap: "12px",
        },
        outerCircle: {
            background:
                "radial-gradient(circle at 30% 30%, color-mix(in oklab, var(--olive-leaf) 65%, var(--cornsilk)), var(--forest))",
            width: "174px",
            height: "174px",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "var(--shadow-soft)",
        },
        innerCircle: {
            background: "color-mix(in oklab, var(--card) 94%, var(--cornsilk))",
            borderRadius: "50%",
            width: "128px",
            height: "128px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            color: "var(--black-forest)",
        },
        statusWrapper: {
            display: "flex",
            alignItems: "center",
            gap: "9px",
            background: "color-mix(in oklab, var(--cornsilk) 15%, transparent)",
            borderRadius: "999px",
            padding: "9px 14px",
            width: "100%",
            justifyContent: "center",
            fontSize: "14px",
            fontWeight: "600",
            color: "var(--cornsilk)",
        },
        statusIcon: {
            background: currentStatusColor,
            width: "13px",
            height: "13px",
            borderRadius: "50%",
            animation: isSyncing
                ? "sync-status-blink 1s ease-in-out infinite"
                : "none",
        },
        startButton: {
            background: "var(--gradiant-clay)",
            width: "100%",
            height: "56px",
            color: "var(--card)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            borderRadius: "18px",
            marginTop: "2px",
            fontSize: "17px",
            fontWeight: "700",
            letterSpacing: "0.02em",
            border: "none",
            transition: "transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease",
        },
        startButtonHover: {
            transform: "translateY(-1px)",
            boxShadow: "var(--shadow-soft)",
        },
        syncStatusWrapper: {
            background: "var(--card)",
            padding: "14px",
            borderRadius: "18px",
            textAlign: "left" as const,
            fontSize: "13px",
            border: "var(--card-border)",
            width: "100%",
            boxShadow: "var(--shadow-soft)",
        },
        syncStepGrid: {
            width: "100%",
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: "8px",
        },
        syncStepCard: {
            borderRadius: "14px",
            background: "var(--gradiant-leaf)",
            padding: "10px 8px",
            display: "flex",
            flexDirection: "column" as const,
            gap: "6px",
            alignItems: "flex-start",
            boxShadow: "var(--shadow-soft)",
        },
        syncStepIconWrap: {
            width: "24px",
            height: "24px",
            borderRadius: "999px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
        },
        syncStepTitle: {
            fontSize: "12px",
            fontWeight: "700",
            color: "var(--cornsilk)",
            letterSpacing: "0.01em",
        },
        syncStepDescription: {
            fontSize: "11px",
            lineHeight: 1.25,
            opacity: 0.8,
            color: "rgba(254, 250, 224, 0.82)",
        },
        syncStatusBarContainer: {
            width: "100%",
            background: "var(--seccondary)",
            height: "11px",
            borderRadius: "30px",
            marginTop: "8px",
            overflow: "hidden",
        },
        syncStatusBarValue: {
            height: "100%",
            width: `${syncProgress}%`,
            borderRadius: "30px",
            background: "var(--gradiant-clay)",
            transition: "width 0.5s ease-in-out",
        },
        statusPositonWrapper: {
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
        },
        actionArea: {
            width: "100%",
            display: "flex",
            flexDirection: "column" as const,
            gap: "14px",
        },
        infoCardWrapper: {
            width: "100%",
        },
        progressMeta: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "13px",
            color: "var(--black-forest)",
            fontWeight: "600",
            marginBottom: "4px",
        },
        progressPill: {
            "fontSize": "11px",
            "fontWeight": "700",
            "borderRadius": "50%",
            "padding": "4px 8px",
            "color": "var(--card)",
            "background": "var(--gradiant-clay)",
            "width": "33px",
            "height": "33px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
        },
        statusRow: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "10px",
            marginBottom: "8px",
            color: "var(--black-forest)",
        },
        statusLeftMeta: {
            display: "flex",
            alignItems: "center",
            gap: "7px",
            fontSize: "12px",
            fontWeight: "600",
            color: "rgba(40, 54, 24, 0.78)",
        },
    };

    return (
        <div>
            <TabHeader
                tab={"SYNC"}
                title={"Pull fresh birds"}
                subTitle={"Get the latest detections from your device."}
            />
            <div style={styles.contentWrapper}>
                <div style={styles.heroCard}>
                    <div style={styles.outerCircle}>
                        <div style={styles.innerCircle}>
                            {isSyncing ? (
                                <Download size={72} aria-hidden="true" />
                            ) : temporaryStatusType === "success" ? (
                                <Check size={72} aria-hidden="true" />
                            ) : (
                                <Wifi size={72} aria-hidden="true" />
                            )}
                        </div>
                    </div>

                    <div style={styles.statusPositonWrapper}>
                        <div style={styles.statusWrapper}>
                            <div style={styles.statusIcon}></div>
                            <div style={{ maxWidth: "92%", textAlign: "center" as const }}>
                                {currentStatusText}
                            </div>
                        </div>
                    </div>
                </div>

                <div style={styles.actionArea}>
                    <div style={styles.syncStepGrid}>
                        {syncSteps.map((step) => {
                            const StepIcon = step.icon;

                            return (
                                <div
                                    key={step.title}
                                    style={styles.syncStepCard}
                                >
                                    <div
                                        style={{
                                            ...styles.syncStepIconWrap,
                                            background: "color-mix(in oklab, var(--cornsilk) 15%, transparent)",
                                            color: "var(--cornsilk)"
                                        }}
                                    >
                                        <StepIcon size={14} />
                                    </div>
                                    <div style={styles.syncStepTitle}>{step.title}</div>
                                    <div style={styles.syncStepDescription}>{step.description}</div>
                                </div>
                            );
                        })}
                    </div>

                    <div style={styles.syncStatusWrapper}>
                        <div style={styles.statusRow}>
                            <div style={styles.statusLeftMeta}>
                                <ShieldCheck size={14} aria-hidden="true" />
                                <span>Secure transfer</span>
                            </div>
                            <div style={styles.progressPill}>{syncProgress}%</div>
                        </div>

                        <div style={styles.progressMeta}>
                            <div>{progressPanelText}</div>
                        </div>

                        <div style={styles.syncStatusBarContainer}>
                            <div style={styles.syncStatusBarValue}></div>
                        </div>
                    </div>

                    <button
                        onClick={startSync}
                        style={{
                            ...styles.startButton,
                            opacity: isSyncing ? 0.6 : 1,
                        }}
                    >
                        <WifiSync size={20} aria-hidden="true" style={{ marginRight: "8px", transform: "translateY(-2px)" }} />
                        {isSyncing ? "Syncing..." : "Start Sync"}
                    </button>
                </div>
            </div>
            {isLoading && <LoadingSpinner />}
        </div>
    );
};

export default Sync;
