import { useState, useEffect } from "react";
import LoadingSpinner from "../../../components/LoadingSpinner"
import { Setting } from "../../../lib/types";
import Switch from "../../../components/Switch";
import SettingsService from "../../../lib/services/SettingsService";

const AdvancedSettings = () => {
    const [loading, setLoading] = useState(false);
    const [settings, setSettings] = useState<Setting[]>([]);

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
    };

    const renderDescription = (setting: Setting) => {
        if (!setting.description) {
            return null;
        }

        if (setting.id === "apprise_input") {
            return (
                <>
                    More here: {" "}
                    <a
                        href="https://github.com/caronc/apprise/wiki"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={styles.descriptionLink}
                    >
                        Apprise Documentation
                    </a>
                </>
            );
        }

        return setting.description;
    };

    const fetchSettings = async () => {
        setLoading(true);
        try {
            const fetchedSettings = await SettingsService.getAllDeviceSettings("ADVANCED");
            setSettings(fetchedSettings);
        } catch (error) {
            console.error("Error fetching settings:", error);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchSettings();
    }, []);

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
        select: {
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
            cursor: "pointer",
        },
        textarea: {
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
            resize: "vertical" as const,
            minHeight: "120px",
            fontFamily: "inherit",
            lineHeight: 1.4,
        },
        descriptionText: {
            fontSize: "12px",
            opacity: "0.6",
            lineHeight: 1.4,
        },
        descriptionLink: {
            color: "var(--black-forest)",
            textDecoration: "underline",
            fontWeight: 600,
        },
    }

    const tabs = Array.from(new Set(settings.map((s) => s.tab)));

    return (
        <div>
            <div style={{ textAlign: "left", marginTop: "-10px" }}>
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
                                                index < filteredSettings.length - 1
                                                    ? "1px solid rgba(40, 54, 24, 0.12)"
                                                    : "none",
                                            paddingBottom:
                                                index < filteredSettings.length - 1
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
                                                <div style={styles.descriptionText}>
                                                    {renderDescription(setting)}
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
                                                    checked={Boolean(setting.value)}
                                                    onChange={(checked) =>
                                                        handleSettingChange(setting.id, checked)
                                                    }
                                                    ariaLabel={`Toggle ${setting.name}`}
                                                />
                                            ) : setting.type === "select" ? (
                                                <select
                                                    value={String(setting.value)}
                                                    onChange={(e) =>
                                                        handleSettingChange(setting.id, e.target.value)
                                                    }
                                                    style={{
                                                        ...styles.select,
                                                        opacity: setting.disabled ? 0.6 : 1,
                                                    }}
                                                    disabled={setting?.disabled === true}
                                                >
                                                    {setting.selectOptions?.map((opt) => (
                                                        <option key={String(opt.value)} value={String(opt.value)}>
                                                            {opt.label}
                                                        </option>
                                                    ))}
                                                </select>
                                            ) : setting.type === "textarea" ? (
                                                <textarea
                                                    value={String(setting.value)}
                                                    onChange={(e) =>
                                                        handleSettingChange(setting.id, e.target.value)
                                                    }
                                                    style={{
                                                        ...styles.textarea,
                                                        opacity: setting.disabled ? 0.6 : 1,
                                                    }}
                                                    disabled={setting?.disabled === true}
                                                />
                                            ) : (
                                                <input
                                                    type={setting.type === "number" ? "number" : "text"}
                                                    value={String(setting.value)}
                                                    onChange={(e) =>
                                                        handleSettingChange(
                                                            setting.id,
                                                            setting.type === "number"
                                                                ? Number(e.target.value)
                                                                : e.target.value,
                                                        )
                                                    }
                                                    min={setting.min}
                                                    max={setting.max}
                                                    step={setting.step}
                                                    style={{
                                                        ...styles.input,
                                                        opacity: setting.disabled ? 0.6 : 1,
                                                    }}
                                                    disabled={setting?.disabled === true}
                                                />
                                            )}
                                        </div>
                                    </div>
                                ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Helper to fix scrolling */}
            <div style={{ paddingBottom: "90px" }}></div>

            {loading && <LoadingSpinner />}
        </div>
    )
}

export default AdvancedSettings