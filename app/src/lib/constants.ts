export const SYNC_ROW_LIMIT = 20;
export const BASE_URL = "https://192-168-4-1.sslip.io";
export const CERTIFICATE_URL = "https://192-168-4-1.sslip.io/cert";
export const CERTIFICATE_URL_FALLBACK = "http://192.168.4.1/cert";
export const BIRDWEATHER_BASE_URL = "https://app.birdweather.com/api/v1/";

export const getCertificateUrl = () =>
    typeof window !== "undefined" && window.isSecureContext
        ? CERTIFICATE_URL
        : CERTIFICATE_URL_FALLBACK;
