import TabHeader from "../../components/TabHeader";
import { DeviceInfo } from "../../../lib/types";
import { useState } from "react";
import DeviceInfoCard from "./DeviceInfoCard";

const Settings = () => {
    const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>({
        name: "Raspberry Pi 4",
        battery: 85,
        storage: 64,
        uptime: 12,
    });

    return (
        <div>
            <TabHeader tab={"SETTINGS"} title={"Preferences"} subTitle={""} />
            <DeviceInfoCard deviceInfo={deviceInfo} />
        </div>
    );
};

export default Settings;
