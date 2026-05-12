import { API_BASE_URL } from "../constants";

export default class ApiService {
    static async callApi(path: string, pathParams?: Record<string, any>) {
        let url = `${API_BASE_URL}${path}`;
        if (pathParams) {
            const queryString = new URLSearchParams(pathParams).toString();
            url += `?${queryString}`;
        }
        const response = await fetch(url);
        if (!response.ok) {
            return false;
        }

        return await response.json();
    }
}
