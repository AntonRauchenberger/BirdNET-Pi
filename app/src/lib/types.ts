export interface DeviceDetails {
    name: string;
    battery: number;
    storage: number;
    uptime: number;
    ssid: string;
    longitude?: number;
    latitude?: number;
    lastUpdate?: string;
}

export interface Setting {
    id: string;
    name: string;
    description: string | null;
    value: boolean | string | number;
    setValue?: ((value: boolean | string | number) => void) | undefined;
    tab?: string;
    topTab?: string;
    type?: "boolean" | "string" | "number" | "select" | "textarea";
    selectOptions?: { label: string; value: string | number }[];
    icon?: React.ReactNode;
    disabled?: boolean;
    defaultValue?: boolean | string | number;
    deviceInternal?: boolean;
    max?: number;
    min?: number;
    step?: number;
}

export interface Species {
    commonName: string;
    scientificName: string;
    avgConfidence: number;
    detections: number;
    lastCall: number;
    latitude: number;
    longitude: number;
    firstSeen: number;
    fileName: string;
    imageUrl?: string;
}

export interface Detection {
    id?: number;
    date: number;
    time: number;
    scientificName: string;
    commonName: string;
    confidence: number;
    latitude: number;
    longitude: number;
    cutoff: number;
    week: number;
    sens: number;
    overlap: number;
    fileName: string;
}
