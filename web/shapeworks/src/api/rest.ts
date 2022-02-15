import { Dataset } from "@/types";
import { apiClient } from "./auth";

export async function getDatasets(): Promise<Dataset[]>{
    return (await apiClient.get('/datasets')).data.results
}
