import TabHeader from "../../components/TabHeader";
import { DeviceInfo, Setting } from "../../../lib/types";
import { useState } from "react";
import DeviceInfoCard from "./DeviceInfoCard";
import { Wifi, RefreshCw, KeyRound } from "lucide-react";
import Switch from "../../components/Switch";

const Settings = () => {
    const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>({
        name: "Raspberry Pi 4",
        battery: 85,
        storage: 64,
        uptime: 12,
    });
    const [settings, setSettings] = useState<Setting[]>([
        {
            id: "connection",
            name: "Connection",
            description: "Manage your device's connection settings",
            value: "MeinBirdNET",
            setValue: undefined,
            tab: "SYNCING",
            type: "string",
            icon: <Wifi size={18} />,
            disabled: true,
        },
        {
            id: "sync",
            name: "Enable sync",
            description: "Sync your data with the cloud",
            value: true,
            setValue: (value: boolean | string | number) => {
                setSettings((prevSettings) =>
                    prevSettings.map((setting) =>
                        setting.id === "sync" ? { ...setting, value } : setting,
                    ),
                );
            },
            tab: "SYNCING",
            type: "boolean",
            icon: <RefreshCw size={18} />,
        },
        {
            id: "deleteSyncedData",
            name: "Delete synced data",
            description:
                "Delete your data from the device after successful sync",
            value: false,
            setValue: (value: boolean | string | number) => {
                setSettings((prevSettings) =>
                    prevSettings.map((setting) =>
                        setting.id === "deleteSyncedData"
                            ? { ...setting, value }
                            : setting,
                    ),
                );
            },
            tab: "SYNCING",
            type: "boolean",
            icon: <RefreshCw size={18} />,
        },
        {
            id: "mapTilerApiKey",
            name: "MapTiler API Key",
            description: "Manage your device's credentials",
            value: "1234sada1231",
            setValue: (value: boolean | string | number) => {
                setSettings((prevSettings) =>
                    prevSettings.map((setting) =>
                        setting.id === "mapTilerApiKey"
                            ? { ...setting, value }
                            : setting,
                    ),
                );
            },
            tab: "CREDENTIALS",
            type: "string",
            icon: <KeyRound size={18} />,
            disabled: false,
        },
    ]);

    const styles = {
        tabHeader: {
            letterSpacing: "1px",
            fontWeight: "600",
            textAlign: "left" as const,
            fontSize: "15px",
            marginTop: "20px",
            marginBottom: "5px",
        },
        tabCard: {
            background: "var(--card)",
            border: "var(--card-border)",
            padding: "1.25rem",
            borderRadius: "1.5rem",
            boxShadow: "var(--shadow-soft)",
            display: "flex",
            flexDirection: "column" as const,
            gap: "15px",
        },
        settingRow: {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
        },
        settingNameWrapper: {
            display: "flex",
            gap: "8px",
            alignItems: "center",
        },
        settingIcon: {
            height: "35px",
            width: "35px",
            borderRadius: "50%",
            backgroundColor: "var(--black-forest)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            color: "var(--card)",
        },
        settingValueWrapper: {
            width: "30%",
            display: "flex",
            justifyContent: "end",
        },
        input: {
            background: "none",
            color: "inherit",
            border: "none",
            opacity: "0.7",
            width: "100%",
        },
    };

    return (
        <div>
            <TabHeader tab={"SETTINGS"} title={"Preferences"} subTitle={""} />
            <DeviceInfoCard deviceInfo={deviceInfo} />
            <div style={{ textAlign: "left" }}>
                <div>
                    <div style={styles.tabHeader}>SYNCING</div>
                    <div style={styles.tabCard}>
                        {settings
                            .filter((setting) => setting.tab === "SYNCING")
                            .map((setting) => (
                                <div key={setting.id} style={styles.settingRow}>
                                    <div style={styles.settingNameWrapper}>
                                        <div style={styles.settingIcon}>
                                            {setting.icon}
                                        </div>
                                        <div>{setting.name}</div>
                                    </div>
                                    <div style={styles.settingValueWrapper}>
                                        {setting.type === "boolean" ? (
                                            <Switch
                                                checked={Boolean(setting.value)}
                                                onChange={(checked) =>
                                                    setting.setValue?.(checked)
                                                }
                                                ariaLabel={`Toggle ${setting.name}`}
                                            />
                                        ) : (
                                            <input
                                                type="text"
                                                value={String(setting.value)}
                                                onChange={(e) =>
                                                    setting.setValue?.(
                                                        e.target.value,
                                                    )
                                                }
                                                style={styles.input}
                                                disabled={
                                                    setting?.disabled === true
                                                }
                                            />
                                        )}
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>

                <div>
                    <div style={styles.tabHeader}>CREDENTIALS</div>
                    <div style={styles.tabCard}>
                        {settings
                            .filter((setting) => setting.tab === "CREDENTIALS")
                            .map((setting) => (
                                <div key={setting.id} style={styles.settingRow}>
                                    <div style={styles.settingNameWrapper}>
                                        <div style={styles.settingIcon}>
                                            {setting.icon}
                                        </div>
                                        <div>{setting.name}</div>
                                    </div>
                                    <div style={styles.settingValueWrapper}>
                                        {setting.type === "boolean" ? (
                                            <Switch
                                                checked={Boolean(setting.value)}
                                                onChange={(checked) =>
                                                    setting.setValue?.(checked)
                                                }
                                                ariaLabel={`Toggle ${setting.name}`}
                                            />
                                        ) : (
                                            <input
                                                type="text"
                                                value={String(setting.value)}
                                                onChange={(e) =>
                                                    setting.setValue?.(
                                                        e.target.value,
                                                    )
                                                }
                                                style={styles.input}
                                                disabled={
                                                    setting?.disabled === true
                                                }
                                            />
                                        )}
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
