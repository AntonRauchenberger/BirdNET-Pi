import TabHeader from "../../components/TabHeader";
import { DeviceDetails, Setting } from "../../lib/types";
import { useState, useEffect } from "react";
import DeviceInfoCard from "./DeviceInfoCard";
import Switch from "../../components/Switch";
import SettingsService from "../../lib/services/SettingsService";
import DeviceService from "../../lib/services/DeviceService";

const Settings = () => {
    const [deviceInfo, setDeviceInfo] = useState<DeviceDetails>({
        name: "Not connected",
        battery: 0,
        storage: 0,
        uptime: 0,
        ssid: "",
    });
    const [settings, setSettings] = useState<Setting[]>([]);
    const [loading, setLoading] = useState(true);

    const loadSettings = async () => {
        setLoading(true);
        await SettingsService.initializeDefaultSettings();
        const loadedSettings = await SettingsService.getAllSettings();
        setSettings(loadedSettings);

        const deviceDetails = await DeviceService.getDeviceDetails();
        setDeviceInfo(deviceDetails);

        // set connection setting value locally
        setSettings((prevSettings) =>
            prevSettings.map((setting) =>
                setting.id === "connection"
                    ? {
                          ...setting,
                          value: deviceDetails.ssid,
                      }
                    : setting,
            ),
        );

        setLoading(false);
    };

    // Load settings from database on component mount
    useEffect(() => {
        loadSettings();
    }, []);

    // Handle setting value change - directly save to database
    const handleSettingChange = async (
        id: string,
        newValue: boolean | string | number,
    ) => {
        // Update UI immediately
        setSettings((prevSettings) =>
            prevSettings.map((setting) =>
                setting.id === id ? { ...setting, value: newValue } : setting,
            ),
        );

        // Save to database
        await SettingsService.updateSetting(id, newValue);
    };

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
        },
        settingRow: {
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            minHeight: "60px",
            padding: "8px 0",
        },
        settingNameWrapper: {
            display: "flex",
            gap: "12px",
            alignItems: "center",
            flex: 1,
            minWidth: 0,
            width: "100%",
        },
        settingIcon: {
            height: "44px",
            width: "44px",
            minWidth: "44px",
            minHeight: "44px",
            borderRadius: "50%",
            backgroundColor: "var(--black-forest)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            color: "var(--card)",
            flexShrink: 0,
        },
        settingValueWrapper: {
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            minWidth: "120px",
            paddingLeft: "12px",
        },
        input: {
            background: "rgba(255, 255, 255, 0.8)",
            color: "inherit",
            border: "1px solid rgba(40, 54, 24, 0.2)",
            borderRadius: "8px",
            padding: "10px 12px",
            width: "100%",
            fontSize: "14px",
            fontWeight: "500",
            transition: "border-color 0.2s ease",
            minWidth: "299px",
        },
    };

    if (loading) {
        return <div>Loading settings...</div>;
    }

    // Get unique tabs from settings
    const tabs = Array.from(new Set(settings.map((s) => s.tab)));

    return (
        <div>
            <TabHeader tab={"SETTINGS"} title={"Preferences"} subTitle={""} />
            <DeviceInfoCard
                deviceInfo={deviceInfo}
                loadSettings={loadSettings}
            />
            <div style={{ textAlign: "left" }}>
                {tabs.map((tab) => (
                    <div key={tab}>
                        <div style={styles.tabHeader}>{tab}</div>
                        <div style={styles.tabCard}>
                            {settings
                                .filter((setting) => setting.tab === tab)
                                .map((setting, index, filteredSettings) => (
                                    <div
                                        key={setting.id}
                                        style={{
                                            ...styles.settingRow,
                                            flexDirection:
                                                setting.type === "boolean"
                                                    ? "row"
                                                    : "column",
                                            borderBottom:
                                                index <
                                                filteredSettings.length - 1
                                                    ? "1px solid rgba(40, 54, 24, 0.12)"
                                                    : "none",
                                            paddingBottom:
                                                index <
                                                filteredSettings.length - 1
                                                    ? "16px"
                                                    : "0",
                                        }}
                                    >
                                        <div style={styles.settingNameWrapper}>
                                            <div style={styles.settingIcon}>
                                                {setting.icon}
                                            </div>
                                            <div>
                                                <div>{setting.name}</div>
                                                <div
                                                    style={{
                                                        fontSize: "12px",
                                                        opacity: "0.6",
                                                    }}
                                                >
                                                    {setting.description}
                                                </div>
                                            </div>
                                        </div>
                                        <div
                                            style={{
                                                ...styles.settingValueWrapper,
                                                width:
                                                    setting.type === "boolean"
                                                        ? "auto"
                                                        : "100%",
                                                marginTop:
                                                    setting.type === "boolean"
                                                        ? "0"
                                                        : "8px",
                                                minWidth:
                                                    setting.type === "boolean"
                                                        ? "0px"
                                                        : "120px",
                                            }}
                                        >
                                            {setting.type === "boolean" ? (
                                                <Switch
                                                    checked={Boolean(
                                                        setting.value,
                                                    )}
                                                    onChange={(checked) =>
                                                        handleSettingChange(
                                                            setting.id,
                                                            checked,
                                                        )
                                                    }
                                                    ariaLabel={`Toggle ${setting.name}`}
                                                />
                                            ) : (
                                                <input
                                                    type="text"
                                                    value={String(
                                                        setting.value,
                                                    )}
                                                    onChange={(e) =>
                                                        handleSettingChange(
                                                            setting.id,
                                                            e.target.value,
                                                        )
                                                    }
                                                    style={{
                                                        ...styles.input,
                                                        opacity:
                                                            setting.disabled
                                                                ? 0.6
                                                                : 1,
                                                    }}
                                                    disabled={
                                                        setting?.disabled ===
                                                        true
                                                    }
                                                />
                                            )}
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Settings;
