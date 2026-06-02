import { BenchmarkReport, DeviceDetails } from "../types";
import ApiService from "./ApiService";
import DatabaseService from "./DatabaseService";
import SettingsService from "./SettingsService";

export default class DeviceService {
    private static toNumberOrUndefined(value: unknown): number | undefined {
        if (typeof value === "number" && Number.isFinite(value)) {
            return value;
        }

        if (typeof value === "string") {
            const parsed = Number(value);
            if (Number.isFinite(parsed)) {
                return parsed;
            }
        }

        return undefined;
    }

    static async getDeviceDetails(): Promise<DeviceDetails> {
        const responseData = await ApiService.callApi("/device/details");

        if (responseData === false) {
            return {
                name: "Not connected",
                battery: 0,
                storage: 0,
                uptime: 0,
                ssid: "",
                longitude: undefined,
                latitude: undefined,
                lastUpdate: undefined,
            };
        }

        const normalizedDeviceDetails: DeviceDetails = {
            name:
                typeof responseData.name === "string"
                    ? responseData.name
                    : "Not connected",
            battery: this.toNumberOrUndefined(responseData.battery) ?? 0,
            storage: this.toNumberOrUndefined(responseData.storage) ?? 0,
            uptime: this.toNumberOrUndefined(responseData.uptime) ?? 0,
            ssid:
                typeof responseData.ssid === "string" ? responseData.ssid : "",
            longitude: this.toNumberOrUndefined(responseData.longitude),
            latitude: this.toNumberOrUndefined(responseData.latitude),
            lastUpdate:
                typeof responseData.lastUpdate === "string"
                    ? responseData.lastUpdate
                    : undefined,
        };

        await DatabaseService.saveSingleRowToDatabase(
            "lastKnownDeviceInfo",
            normalizedDeviceDetails,
        );

        return normalizedDeviceDetails;
    }

    static async getBenchmarkReports(): Promise<BenchmarkReport[]> {
        const responseData = await ApiService.callApi("/device/benchmarking/reports");

        if (!Array.isArray(responseData)) {
            return [];
        }

        const normalizedReports: BenchmarkReport[] = responseData.map(
            (reportData) => ({
                datetime:
                    typeof reportData.datetime === "string"
                        ? reportData.datetime
                        : "Unknown date",
                fileType:
                    typeof reportData.fileType === "string"
                        ? reportData.fileType
                        : "unknown",
                fileSize: this.toNumberOrUndefined(reportData.fileSize) ?? 0,
                fileName:
                    typeof reportData.fileName === "string"
                        ? reportData.fileName
                        : "unknown",
                scenario:
                    typeof reportData.scenario === "string"
                        ? reportData.scenario
                        : undefined,
            }),
        );

        return normalizedReports;
    }

    static async downloadBenchmarkReport(report: BenchmarkReport): Promise<Blob | null> {
        try {
            const response = await ApiService.getAudioFile("/device/benchmarking/download", {
                scenario: report.scenario,
                file_name: report.fileName,
            });
            if (response === false || response === null) {
                console.error("Failed to download report.");
                return null;
            }

            const blob = await response.blob();
            return blob;
        } catch (error) {
            console.error("Error downloading report:", error);
            return null;
        }
    }

    static async startBenchmarking(): Promise<void> {
        const scenarioSetting = await SettingsService.getSetting("scenarioName");
        const scenarioName =
            typeof scenarioSetting?.value === "string" && scenarioSetting.value.trim()
                ? scenarioSetting.value.trim()
                : "App Test";

        await ApiService.callApi(
            "/device/benchmarking/start",
            {
                scenario: scenarioName,
            },
            "POST",
        );
    }
}
