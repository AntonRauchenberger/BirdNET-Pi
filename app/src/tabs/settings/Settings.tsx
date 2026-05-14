import { Setting } from "../../lib/types";
import { Wifi, RefreshCw, KeyRound } from "lucide-react";

export const DEFAULT_SETTINGS: Setting[] = [
    {
        id: "connection",
        name: "Connection",
        description: "Shows your device's connection name",
        defaultValue: "MeinBirdNET",
        tab: "SYNCING",
        type: "string",
        icon: <Wifi size={18} />,
        disabled: true,
        value: "MeinBirdNET",
    },
    {
        id: "deleteSyncedData",
        name: "Delete synced data",
        description: "Delete your data from the device after successful sync",
        defaultValue: false,
        tab: "SYNCING",
        type: "boolean",
        icon: <RefreshCw size={18} />,
        value: false,
    },
    {
        id: "mapTilerApiKey",
        name: "MapTiler API Key",
        description: "Manage your device's credentials",
        defaultValue: "",
        tab: "CREDENTIALS",
        type: "string",
        icon: <KeyRound size={18} />,
        value: "",
    },
];
