import TabHeader from "../../components/TabHeader";
import { DeviceDetails, Setting } from "../../lib/types";
import { useState, useEffect } from "react";
import DeviceInfoCard from "./DeviceInfoCard";
import DeviceSettings from "./DeviceSettings";
import Switch from "../../components/Switch";
import LoadingSpinner from "../../components/LoadingSpinner";
import SettingsService from "../../lib/services/SettingsService";
import DeviceService from "../../lib/services/DeviceService";
import { ChevronRight, HardDriveUpload, RotateCw, ShieldCheck } from "lucide-react";
import SubPage from "../../components/SubPage";
import { getCertificateUrl } from "../../lib/constants";

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
    const [activeSubPage, setActiveSubPage] = useState<
        "basic" | "advanced" | null
    >(null);
    const [subPageVisible, setSubPageVisible] = useState(false);
    const [subPageLoading, setSubPageLoading] = useState(false);
    const [subPageSettings, setSubPageSettings] = useState<Setting[]>([]);

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

    const openSubPage = (subPage: "basic" | "advanced") => {
        if (deviceInfo.name === "Not connected") {
            return;
        }

        setSubPageVisible(false);
        setActiveSubPage(subPage);
    };

    const closeSubPage = () => {
        setSubPageVisible(false);
        window.setTimeout(() => {
            setActiveSubPage(null);
        }, 280);
    };

    const fetchSubpageSettings = async () => {
        setSubPageLoading(true);
        try {
            if (!activeSubPage) {
                throw new Error("No active subpage to fetch settings for");
            }

            const fetchedSettings = await SettingsService.getAllDeviceSettings(activeSubPage.toUpperCase());
            setSubPageSettings(fetchedSettings);
        } catch (error) {
            console.error("Error fetching settings:", error);
        } finally {
            setSubPageLoading(false);
        }
    }

    const saveSubpageSettings = async () => {
        setSubPageLoading(true);
        try {
            if (!activeSubPage) {
                throw new Error("No active subpage to save settings for");
            }

            await SettingsService.updateDeviceSettings(subPageSettings);

        } catch (error) {
            console.error("Error saving settings:", error);
        } finally {
            setSubPageLoading(false);
        }
    }

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
            boxShadow: activeSubPage === null ? "var(--shadow-soft)" : "none",
            display: "flex",
            flexDirection: "column" as const,
            paddingTop: "1rem",
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
        subSettingRow: {
            "display": "flex",
            "justifyContent": "space-between",
            "width": "100%",
            "background": "var(--gradiant-leaf)",
            "color": "var(--card)",
            "padding": "1rem",
            "borderRadius": "1.15rem",
            "boxShadow": activeSubPage === null ? "var(--shadow-soft)" : "none",
            "opacity": deviceInfo?.name !== "Not connected" ? 1 : 0.5,
        },
        subSettingName: {
            "fontSize": "18px",
            "fontWeight": "600",
            "transform": "translateY(3px)"
        },
        subSettingIcon: {
            "transform": "translateY(3px)"
        },
        subSettingsWrapper: {
            "display": "flex",
            "flexDirection": "column" as const,
            "gap": "10px"
        },
        refreshButton: {
            "background": "var(--gradiant-clay)",
            "borderRadius": "15px",
            "height": "48px",
            "width": "48px",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center"
        },
        buttonsWrapper: {
            "display": "flex",
            "justifyContent": "flex-end",
            "gap": "8px",
            "alignItems": "center",
        },
        saveButton: {
            "display": "flex",
            "gap": "5px",
            "background": "green",
            "color": "var(--card)",
            "alignItems": "center",
            "padding": "12px",
            "borderRadius": "15px",
            "fontSize": "19px",
            "justifyContent": "center",
            "fontWeight": 600,
        },
        saveIcon: {
            "transform": "translateY(2px)"
        },
        downloadButton: {
            "display": "flex",
            "width": "100%",
            "justifyContent": "center",
            "alignItems": "center",
            "background": "var(--gradiant-clay)",
            "color": "var(--card)",
            "gap": "5px",
            "padding": "10px",
            "borderRadius": "15px",
            "marginTop": "10px",
            "textDecoration": "none",
        },
        linkText: {
            "color": "var(--card)",
            "fontSize": "18px",
            "fontWeight": 600,
        }
    };

    const subPageHeaderButtons = (
        <div style={styles.buttonsWrapper}>
            <div style={styles.saveButton} onClick={() => saveSubpageSettings()}>
                <div style={styles.saveIcon}>
                    <HardDriveUpload
                        size={20}
                    />
                </div>
                <div>Speichern</div>
            </div>

            <div style={styles.refreshButton} onClick={() => fetchSubpageSettings()}>
                <RotateCw
                    size={22}
                    aria-hidden="true"
                    style={{ color: "var(--cornsilk)" }}
                />
            </div>
        </div>
    )

    // Get unique tabs from settings
    const tabs = Array.from(new Set(settings.map((s) => s.tab)));
    const certificateUrl = getCertificateUrl();

    return (
        <div style={{ position: "relative", minHeight: "100vh" }}>
            <div className={loading ? "loading-content-blurred" : ""}>
                <TabHeader
                    tab={"SETTINGS"}
                    title={"Preferences"}
                    subTitle={""}
                />
                <DeviceInfoCard
                    deviceInfo={deviceInfo}
                    loadSettings={loadSettings}
                    activeSubPage={activeSubPage}
                />

                <a style={styles.downloadButton} href={certificateUrl}>
                    <div style={{ transform: "translateY(2px)" }}>
                        <ShieldCheck
                            size={24}
                        />
                    </div>
                    <div style={styles.linkText}>Download Certificate</div>
                </a>

                <div style={{ textAlign: "left" }}>
                    <div>
                        <div style={styles.tabHeader}>DEVICE SETTINGS</div>
                        <div style={styles.subSettingsWrapper}>
                            <div style={styles.subSettingRow} onClick={() => openSubPage("basic")}>
                                <div style={styles.subSettingName}>Basic Settings</div>
                                <div style={styles.subSettingIcon}><ChevronRight size={24} /></div>
                            </div>

                            <div style={styles.subSettingRow} onClick={() => openSubPage("advanced")}>
                                <div style={styles.subSettingName}>Advanced Settings</div>
                                <div style={styles.subSettingIcon}><ChevronRight size={24} /></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div style={{ textAlign: "left" }}>
                    {tabs.map((tab) => (
                        <div key={tab}>
                            <div style={styles.tabHeader}>{tab}</div>
                            <div style={styles.tabCard}>
                                {settings
                                    .filter((setting) => setting.tab === tab && setting.deviceInternal !== true)
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
                                            <div
                                                style={
                                                    styles.settingNameWrapper
                                                }
                                            >
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
                                                        setting.type ===
                                                            "boolean"
                                                            ? "auto"
                                                            : "100%",
                                                    marginTop:
                                                        setting.type ===
                                                            "boolean"
                                                            ? "0"
                                                            : "8px",
                                                    minWidth:
                                                        setting.type ===
                                                            "boolean"
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
            {loading && <LoadingSpinner />}

            {activeSubPage && (
                <SubPage
                    subPageVisible={subPageVisible}
                    closeSubPage={closeSubPage}
                    activeSubPage={
                        <DeviceSettings
                            loading={subPageLoading}
                            settings={subPageSettings}
                            setSettings={setSubPageSettings}
                            setLoading={setSubPageLoading}
                            fetchSettings={fetchSubpageSettings}
                        />
                    }
                    setSubPageVisible={setSubPageVisible}
                    headerElement={subPageHeaderButtons}
                />
            )}
        </div>
    );
};

export default Settings;
