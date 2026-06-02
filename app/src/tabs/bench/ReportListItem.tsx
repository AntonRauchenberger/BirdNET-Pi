import { BenchmarkReport } from "../../lib/types";
import { Download, FileChartColumn, HardDrive } from "lucide-react";

const ReportListItem = (props: {
    report: BenchmarkReport;
    downloadReport: (report: BenchmarkReport) => void;
}) => {

    const removeSeccondsFromDatetime = (datetime: string) => {
        if (datetime.includes("NaN") || isNaN(Date.parse(datetime))) {
            return "Unknown date";
        }

        const date = new Date(datetime);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const hours = String(date.getHours()).padStart(2, "0");
        const minutes = String(date.getMinutes()).padStart(2, "0");
        return `${year}-${month}-${day} ${hours}:${minutes}`;
    }

    const bytesToMegabytes = (bytes: number) => {
        return (bytes / (1024 * 1024)).toFixed(2);
    }

    const styles = {
        card: {
            display: "flex",
            alignItems: "center",
            background: "var(--card)",
            borderRadius: "1.5rem",
            padding: "0.7rem",
            boxShadow: "var(--shadow-soft)",
            border: "var(--card-border)",
            gap: "10px",
            justifyContent: "space-between"
        },
        imageContainer: {
            width: "55px",
            height: "55px",
            background: "var(--copper)",
            backgroundColor:
                "color-mix(in oklab, var(--copper) 15%, transparent)",
            borderRadius: "20px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            overflow: "hidden",
        },
        timestamp: {
            fontWeight: "500",
            fontSize: "19px",
        },
        overviewWrapper: {
            "display": "flex",
            "gap": "10px",
            "alignItems": "center"
        },
        detailsWrapper: {
            "display": "flex",
            "gap": "5px",
            "alignItems": "center",
            "opacity": "0.7",
            "fontSize": "14px"
        },
        downloadButton: {
            "display": "flex",
            "gap": "5px",
            "background": "var(--gradiant-clay)",
            "color": "white",
            "padding": "5px 10px",
            "borderRadius": "12px",
            "fontSize": "15px",
            "fontWeight": "500",
            "alignItems": "center",
            "justifyContent": "center",
            "width": "87px",
        }
    };

    return (
        <div style={styles.card}>
            <div style={styles.overviewWrapper}>
                <div style={styles.imageContainer}>
                    <FileChartColumn size={25} />
                </div>
                <div>
                    <div style={styles.timestamp}>
                        {removeSeccondsFromDatetime(props.report.datetime)}
                    </div>
                    <div style={styles.detailsWrapper}>
                        <div style={{ transform: "translateY(2px)" }}>
                            <HardDrive size={15} />
                        </div>
                        <div>{bytesToMegabytes(props.report.fileSize)} MB</div>
                        <div> · {props.report.scenario}</div>
                    </div>
                </div>
            </div>
            <div style={styles.downloadButton} onClick={() => props.downloadReport(props.report)}>
                <div style={{ transform: "translateY(3px)" }}>
                    <Download size={20} />
                </div>
                <div>
                    {props.report.fileType.toUpperCase()}
                </div>
            </div>
        </div>
    );
};

export default ReportListItem;
