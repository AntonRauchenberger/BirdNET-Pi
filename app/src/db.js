import Dexie from "dexie";

export const db = new Dexie("BirdDetectionsDB");

db.version(1).stores({
    detections: `
    ++id,
    date,
    time,
    scientificName,
    commonName,
    confidence,
    latitude,
    longitude,
    cutoff,
    week,
    sens,
    overlap,
    fileName,
    syncedToBirdWeather,
    uncommon,
    [date+time]
  `,
    settings: `
    id,
    name,
    description,
    value,
    tab,
    type,
    icon,
    disabled,
    defaultValue
  `,
    lastKnownDeviceInfo: `
    ++id,
    name,
    battery,
    storage,
    uptime,
    ssid,
    longitude,
    latitude,
    lastUpdate
  `,
    birdSongs: `
    ++id,
    species,
    timestamp,
    audioBlob
  `,
});
