import { DataObject, Dataset, Subject } from "@/types";
import { apiClient } from "./auth";
import { particlesForOriginalDataObjects } from "@/store";

export async function getDatasets(): Promise<Dataset[]>{
    return (await apiClient.get('/datasets')).data.results
}

export async function getDataset(datasetId: number): Promise<Dataset>{
    return (await apiClient.get(`/datasets/${datasetId}`)).data
}

export async function getSubjectsForDataset(datasetId: number): Promise<Subject[]> {
    return (await apiClient.get('/subjects', {
        params: {dataset: datasetId}
    })).data.results
}

export async function getSubject(subjectId: number): Promise<Subject>{
    return (await apiClient.get(`/subjects/${subjectId}`)).data
}

export async function getDataObjectsForSubject(subjectId: number): Promise<DataObject[]> {
    const dataTypes = ['image', 'segmentation', 'mesh']
    return (await Promise.all(dataTypes.map((type) => {
        return apiClient.get(`/${type}${type == 'mesh' ?'es' :'s'}/`, {
            params: {subject: subjectId}
        })
    }))).map((response, index) => {
        return response.data.results.map((result: DataObject) => {
            const type = dataTypes[index]
            if(type !== 'image'){
                // don't await this, let particles load in after
                getOptimizedParticlesForDataObject(type, result.id)
            }
            return Object.assign(result, {type})
        })
    }).flat(2)
}

export async function getOptimizedParticlesForDataObject(type: string, id: number){
    let particles = (await apiClient.get('/optimized-particles', {
        params: {[`original_${type}`]: id}
    })).data.results
    if (particles.length > 0) particles = particles[0]
    if(!particlesForOriginalDataObjects.value[type]){
        particlesForOriginalDataObjects.value[type] = {}
    }
    particlesForOriginalDataObjects.value[type][id] = particles
}
