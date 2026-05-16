import { BASE_URL } from "../constants";

export default class ApiService {
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

            return false;
        } catch (error) {
            console.warn(
                `API call failed for ${method} ${url.toString()}:`,
                error,
            );
        }

        return false;
    }
}
