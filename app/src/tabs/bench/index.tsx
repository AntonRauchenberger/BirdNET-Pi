import { useState } from "react";
import InfoCard from "../../components/InfoCard";
import TabHeader from "../../components/TabHeader";
import { BenchmarkReport, DeviceDetails } from "../../lib/types";
import TopCard from "./TopCard";
import ReportListItem from "./ReportListItem";
import LoadingSpinner from "../../components/LoadingSpinner";
import { RotateCw } from "lucide-react";


const Bench = () => {
    const [reports, setReports] = useState<BenchmarkReport[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [deviceInfo, setDeviceInfo] = useState<DeviceDetails | null>(null);

    const startBenchmarking = async () => {
        if (!deviceInfo || deviceInfo?.name === "Not connected") {
            return
        }

        console.log("TODO")
    }

    const downloadReport = async (report: BenchmarkReport) => {
        console.log("TODO", report)
    }

    const styles = {
        reportsHeaderWrapper: {
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center"
        },
        reportsHeaderSubWrapper: {
            "display": "flex",
            "alignItems": "center",
            "gap": "10px"
        },
        reportsHeader: {
            "fontSize": "22px",
            "fontWeight": "600",
            "color": "black"
        },
        reportsCounter: {
            "fontSize": "13px",
            "opacity": "0.7"
        },
        reportsWrapper: {
            "marginTop": "15px",
            "display": "flex",
            "flexDirection": "column" as const,
            "gap": "10px"
        },
        fallback: {
            "opacity": "0.6",
            "marginTop": "40px",
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
    }

    return (
        <div>
            <TabHeader
                tab="DIAGNOSTICS"
                title="System Benchmarking"
                subTitle="Run a performance analysis on your device."
            />

            <div style={{ marginTop: "20px" }}>
                <TopCard deviceInfo={deviceInfo} startBenchmarking={startBenchmarking} />
            </div>

            <div style={{ marginTop: "20px" }}>
                <InfoCard text="All reports are saved locally on the device's SD card and can be downloaded fully offline. Device connection required." />
            </div>

            <div style={{ marginTop: "20px" }} >
                <div style={styles.reportsHeaderWrapper}>
                    <div style={styles.reportsHeaderSubWrapper}>
                        <div style={styles.reportsHeader}>
                            Available Reports
                        </div>
                        <div style={styles.refreshButton} onClick={() => { }}>
                            <RotateCw
                                size={20}
                                aria-hidden="true"
                                style={{ color: "var(--cornsilk)" }}
                            />
                        </div>
                    </div>

                    <div style={styles.reportsCounter}>
                        {reports.length} Runs
                    </div>
                </div>

                <div style={styles.reportsWrapper}>
                    {reports.map((report, index) => (
                        <ReportListItem key={index} report={report} downloadReport={downloadReport} />
                    ))}
                    {reports.length === 0 && (
                        <div style={styles.fallback}>
                            No reports available or not connected to device.
                        </div>
                    )}
                </div>
            </div>

            {isLoading && <LoadingSpinner />}
        </div>
    )
};

export default Bench;
