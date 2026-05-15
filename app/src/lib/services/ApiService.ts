export default class ApiService {
    private static getApiOrigins(): string[] {
        const origins: string[] = [window.location.origin];
        const configuredFallback = localStorage.getItem("birdnetApiBaseUrl");
        const hotspotFallback = configuredFallback || "http://192.168.4.1";

        if (!origins.includes(hotspotFallback)) {
            origins.push(hotspotFallback);
        }

        return origins;
    }

    static async callApi(
        path: string,
        pathParams?: Record<string, any>,
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
        body?: unknown,
    ) {
        const normalizedPath = path.startsWith("/") ? path : `/${path}`;
        const origins = this.getApiOrigins();
        for (const origin of origins) {
            const url = new URL(normalizedPath, origin);
            if (pathParams && Object.keys(pathParams).length > 0) {
                for (const [key, value] of Object.entries(pathParams)) {
                    url.searchParams.set(key, String(value));
                }
            }

            try {
                const response = await fetch(url.toString(), {
                    method,
                    headers: body
                        ? {
                              "Content-Type": "application/json",
                          }
                        : undefined,
                    body: body ? JSON.stringify(body) : undefined,
                });

                if (response.ok) {
                    return await response.json();
                }

                // Retry against fallback origin only for temporary/server-side failures.
                if (response.status >= 500) {
                    continue;
                }

                return false;
            } catch (error) {
                console.warn(
                    `API call failed for ${method} ${url.toString()}:`,
                    error,
                );
            }
        }

        return false;
    }
}
