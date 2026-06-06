-- ==========================================
-- Cleanup
-- ==========================================
DROP TABLE IF EXISTS public.detections CASCADE;
DROP TABLE IF EXISTS public.settings CASCADE;
DROP TABLE IF EXISTS public.bird_songs CASCADE;


-- ==========================================
-- Detections
-- ==========================================
CREATE TABLE public.detections (
    id BIGINT PRIMARY KEY, 
    date DATE NOT NULL,
    time TIME NOT NULL,
    "scientificName" TEXT NOT NULL,
    "commonName" TEXT,
    confidence NUMERIC,
    latitude NUMERIC,
    longitude NUMERIC,
    cutoff NUMERIC,
    week INTEGER,
    sens NUMERIC,
    overlap NUMERIC,
    "fileName" TEXT,
    "syncedToBirdWeather" BOOLEAN DEFAULT FALSE,
    uncommon BOOLEAN DEFAULT FALSE,
    "createdAt" TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_detections_date_time ON public.detections (date, time);

ALTER TABLE public.detections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vollzugriff Detections" ON public.detections FOR ALL TO anon USING (true) WITH CHECK (true);


-- ==========================================
-- Settings
-- ==========================================
CREATE TABLE public.settings (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    value TEXT,
    tab TEXT,
    type TEXT,             
    icon TEXT,
    disabled BOOLEAN DEFAULT FALSE,
    "defaultValue" TEXT
);

ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vollzugriff Settings" ON public.settings FOR ALL TO anon USING (true) WITH CHECK (true);


-- ==========================================
-- Bird songs metadata
-- ==========================================
CREATE TABLE public.bird_songs (
    id SERIAL PRIMARY KEY,
    species TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    audio_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.bird_songs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Vollzugriff Bird Songs" ON public.bird_songs FOR ALL TO anon USING (true) WITH CHECK (true);