import { BASE_URL } from "../constants";

export default class ApiService {
    private static readonly REQUEST_TIMEOUT_MS = 5000;

    static async callApi(
        path: string,
        pathParams?: Record<string, any>,
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
        body?: unknown,
        baseUrl?: string,
    ) {
        const normalizedPath = path.startsWith("/") ? path : `/${path}`;
        const url = new URL(normalizedPath, baseUrl || BASE_URL);
        if (pathParams && Object.keys(pathParams).length > 0) {
            for (const [key, value] of Object.entries(pathParams)) {
                url.searchParams.set(key, String(value));
            }
        }

        const controller = new AbortController();
        let timeoutId: ReturnType<typeof setTimeout> | undefined;

        try {
            const timeoutPromise = new Promise<never>((_, reject) => {
                timeoutId = setTimeout(() => {
                    controller.abort();
                    reject(
                        new Error(
                            `API request timed out after ${ApiService.REQUEST_TIMEOUT_MS / 1000} seconds`,
                        ),
                    );
                }, ApiService.REQUEST_TIMEOUT_MS);
            });

            const response = await Promise.race([
                fetch(url.toString(), {
                    method,
                    headers: body
                        ? {
                              "Content-Type": "application/json",
                          }
                        : undefined,
                    body: body ? JSON.stringify(body) : undefined,
                    signal: controller.signal,
                }),
                timeoutPromise,
            ]);

            if (response.ok) {
                return await response.json();
            }

            return false;
        } catch (error) {
            console.warn(
                `API call failed for ${method} ${url.toString()}:`,
                error,
            );
        } finally {
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
        }

        return false;
    }
}
