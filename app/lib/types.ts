export interface DeviceInfo {
    name: string;
    battery: number;
    storage: number;
    uptime: number;
}

export interface Setting {
    id: string;
    name: string;
    description: string | null;
    value: boolean | string | number;
    setValue: ((value: boolean | string | number) => void) | undefined;
    tab?: string;
    type?: "boolean" | "string" | "number";
    icon?: React.ReactNode;
    disabled?: boolean;
}
