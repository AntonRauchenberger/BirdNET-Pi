import { CloudUpload, CloudCheck, CloudAlert, Ban, CloudDownload, Earth } from "lucide-react";

const SyncButtons = (props: {
    startCloudUpload: () => void;
    startBirdWeatherUpload: () => void;
    currentCloudUploadStatus: "idle" | "uploading" | "success" | "error" | "forbidden" | "downloadReady";
    currentBirdWeatherUploadStatus: "idle" | "uploading" | "success" | "error" | "forbidden" | "downloadReady";
}) => {

    const styles = {
        wrapper: {
            "display": "flex",
            "justifyContent": "space-between",
            "gap": "10px",
            "marginTop": "20px",
            "width": "100%",
        },
        card: {
            "background": "var(--gradiant-leaf)",
            "borderRadius": "1.5rem",
            "color": "var(--cornsilk)",
            "overflow": "hidden",
            "padding": "1rem",
            "boxShadow": "var(--shadow-soft)",
            "textAlign": "left" as const,
            "width": "50%",
            "display": "flex",
            "flexDirection": "column" as const,
            "gap": "4px",
        },
        icon: {
            "width": "40px",
            "height": "40px",
            "borderRadius": "50%",
            "background": "color-mix(in oklab, var(--cornsilk) 15%, transparent)",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center"
        },
        title: {
            "fontWeight": "bold",
        },
        subTitle: {
            "fontSize": "13px",
            "opacity": "0.7",
            "fontWeight": "400"
        }
    }

    return (
        <div style={styles.wrapper}>
            <div style={{ ...styles.card, opacity: props.currentCloudUploadStatus === "forbidden" ? 0.7 : 1 }} onClick={props.startCloudUpload}>
                <div style={styles.icon}>
                    {props.currentCloudUploadStatus === "success" ? (
                        <CloudCheck size={20} />
                    ) : props.currentCloudUploadStatus === "downloadReady" ? (
                        <CloudDownload size={20} />
                    ) : props.currentCloudUploadStatus === "forbidden" ? (
                        <Ban size={20} />
                    ) : props.currentCloudUploadStatus === "error" ? (
                        <CloudAlert size={20} />
                    ) : (
                        <CloudUpload size={20} />
                    )}
                </div>

                <div>
                    <div style={styles.title}>
                        Cloud upload
                    </div>
                    <div style={styles.subTitle}>
                        Upload to Supabase
                    </div>
                </div>
            </div>

            <div style={{ ...styles.card, background: "var(--gradiant-clay)", opacity: props.currentBirdWeatherUploadStatus === "forbidden" ? 0.7 : 1 }} onClick={props.startBirdWeatherUpload}>
                <div style={styles.icon}>
                    {props.currentBirdWeatherUploadStatus === "success" ? (
                        <CloudCheck size={20} />
                    ) : props.currentBirdWeatherUploadStatus === "downloadReady" ? (
                        <CloudDownload size={20} />
                    ) : props.currentBirdWeatherUploadStatus === "forbidden" ? (
                        <Ban size={20} />
                    ) : props.currentBirdWeatherUploadStatus === "error" ? (
                        <CloudAlert size={20} />
                    ) : (
                        <Earth size={20} />
                    )}
                </div>

                <div>
                    <div style={styles.title}>
                        BirdWeather
                    </div>
                    <div style={styles.subTitle}>
                        Share to community
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SyncButtons;