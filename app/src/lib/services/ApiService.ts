export default class ApiService {
    static async callApi(
        path: string,
        pathParams?: Record<string, any>,
        method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" = "GET",
        body?: unknown,
    ) {
        let url = `${path}`;
        if (pathParams && Object.keys(pathParams).length > 0) {
            const queryString = new URLSearchParams(pathParams).toString();
            url += `?${queryString}`;
        }

        try {
            const response = await fetch(url, {
                method,
                headers: body
                    ? {
                          "Content-Type": "application/json",
                      }
                    : undefined,
                body: body ? JSON.stringify(body) : undefined,
            });

            if (!response.ok) {
                return false;
            }

            return await response.json();
        } catch (error) {
            console.error(`API call failed for ${method} ${path}:`, error);
            return false;
        }
    }
}
