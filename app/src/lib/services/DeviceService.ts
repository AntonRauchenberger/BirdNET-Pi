import { DeviceDetails } from "../types";
import ApiService from "./ApiService";
import DatabaseService from "./DatabaseService";

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
}
