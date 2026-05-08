import Dexie from "dexie";

export const db = new Dexie("BirdDetectionsDB");

db.version(1).stores({
    detections: `
    ++id,
    Date,
    Time,
    Sci_Name,
    Com_Name,
    Confidence,
    Lat,
    Lon,
    Cutoff,
    Week,
    Sens,
    Overlap,
    File_Name,
    [Date+Time],
    Com_Name,
    Sci_Name
  `,
});
