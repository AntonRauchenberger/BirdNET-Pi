import { DeviceDetails } from "../types";
import ApiService from "./ApiService";

export default class DeviceService {
    static async getDeviceDetails(): Promise<DeviceDetails> {
        const responseData = await ApiService.callApi("/device/details");

        console.log(responseData);

        if (responseData === false) {
            return {
                name: "Not connected",
                battery: 0,
                storage: 0,
                uptime: 0,
                ssid: "",
            };
        }

        return responseData;
    }
}
