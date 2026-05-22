import { db } from "../../db";
import { Setting } from "../types";
import { DEFAULT_SETTINGS } from "../../tabs/settings/Settings";

export default class SettingsService {
    static async getSetting(id: string): Promise<Setting | null> {
        try {
            const setting = await (db as any).settings.get({ id });
            if (setting) {
                return setting;
            }
            // Return default value if not found in database
            const defaultSetting = DEFAULT_SETTINGS.find((s) => s.id === id);
            return defaultSetting || null;
        } catch (error) {
            console.error(`Error getting setting ${id}:`, error);
            const defaultSetting = DEFAULT_SETTINGS.find((s) => s.id === id);
            return defaultSetting || null;
        }
    }

    static async getAllSettings(): Promise<Setting[]> {
        try {
            const dbSettings = await (db as any).settings.toArray();
            const settingMap = new Map(dbSettings.map((s: any) => [s.id, s]));

            // Merge database settings with defaults
            const allSettings = DEFAULT_SETTINGS
                .filter((s) => s.deviceInternal !== true) // Exclude device internal settings
                .map((defaultSetting) => {
                    const dbSetting = settingMap.get(defaultSetting.id) as any;
                    return dbSetting
                        ? { ...defaultSetting, value: dbSetting.value }
                        : defaultSetting;
                });

            return allSettings;
        } catch (error) {
            console.error("Error getting all settings:", error);
            return DEFAULT_SETTINGS;
        }
    }

    static async getAllDeviceSettings(topTab: string): Promise<Setting[]> {
        try {
            const dbSettings = await (db as any).settings.toArray();
            const settingMap = new Map(dbSettings.map((s: any) => [s.id, s]));

            // Filter defaults to this topTab, then merge with any saved DB values
            const allSettings = DEFAULT_SETTINGS
                .filter((s) => s.topTab === topTab)
                .map((defaultSetting) => {
                    const dbSetting = settingMap.get(defaultSetting.id) as any;
                    return dbSetting
                        ? { ...defaultSetting, value: dbSetting.value }
                        : defaultSetting;
                });

            return allSettings;
        } catch (error) {
            console.error("Error getting all device settings:", error);
            return DEFAULT_SETTINGS.filter((s) => s.topTab === topTab);
        }
    }

    static async updateSetting(
        id: string,
        value: boolean | string | number,
    ): Promise<void> {
        try {
            const defaultSetting = DEFAULT_SETTINGS.find((s) => s.id === id);
            if (!defaultSetting) {
                console.error(`Setting ${id} not found in defaults`);
                return;
            }

            const settingToSave = {
                id,
                name: defaultSetting.name,
                description: defaultSetting.description,
                value,
                tab: defaultSetting.tab,
                type: defaultSetting.type,
                disabled: defaultSetting.disabled,
                defaultValue: defaultSetting.defaultValue,
            };

            await (db as any).settings.put(settingToSave);
        } catch (error) {
            console.error(`Error updating setting ${id}:`, error);
        }
    }

    static async initializeDefaultSettings(): Promise<void> {
        try {
            for (const defaultSetting of DEFAULT_SETTINGS) {
                const exists = await (db as any).settings.get({
                    id: defaultSetting.id,
                });
                if (!exists) {
                    await this.updateSetting(
                        defaultSetting.id,
                        defaultSetting.defaultValue || defaultSetting.value,
                    );
                }
            }
        } catch (error) {
            console.error("Error initializing default settings:", error);
        }
    }
}
