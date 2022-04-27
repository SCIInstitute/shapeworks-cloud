import { DataObject, Dataset, Subject, Particles, GroomedShape } from '@/types'
import { getDataset, getGroomedShapeForDataObject, getOptimizedParticlesForDataObject } from '@/api/rest';
import { ref } from '@vue/composition-api'

export const loadingState = ref<boolean>(false)

export const allDatasets = ref<Dataset[]>([])

export const selectedDataset = ref<Dataset>()

export const allSubjectsForDataset = ref<Subject[]>([])

export const allDataObjectsInDataset = ref<DataObject[]>([])

export const selectedDataObjects = ref<DataObject[]>([])

export const particleSize = ref<number>(2)

export const particlesForOriginalDataObjects = ref<Record<string, Record<number, Particles>>>({})

export const groomedShapesForOriginalDataObjects = ref<Record<string, Record<number, GroomedShape>>>({})

export const layers = ref<Record<string, any>[]>([
    { name: 'Original', color: 'white', rgb: [1, 1, 1] },
    { name: 'Groomed', color: 'green', rgb: [0, 1, 0] },
    { name: 'Reconstructed', color: 'red', rgb: [1, 0, 0] },
    { name: 'Particles', color: undefined, rgb: undefined }
])

export const layersShown = ref<string[]>(["Original"])

export const loadDataset = async (datasetId: number) => {
    // Only reload if something has changed
    if (selectedDataset.value?.id != datasetId) {
        loadingState.value = true;
        selectedDataset.value = await getDataset(datasetId);
        loadingState.value = false;
    }
}

export const loadParticlesForObject = async (type: string, id: number) => {
    let particles = await getOptimizedParticlesForDataObject(type, id)
    if (particles.length > 0) particles = particles[0]
    if(!particlesForOriginalDataObjects.value[type]){
        particlesForOriginalDataObjects.value[type] = {}
    }
    particlesForOriginalDataObjects.value[type][id] = particles
}

export const loadGroomedShapeForObject = async (type: string, id: number) => {
    let groomed = await getGroomedShapeForDataObject(type, id)
    if (groomed.length > 0) groomed = groomed[0]
    if(!groomedShapesForOriginalDataObjects.value[type]){
        groomedShapesForOriginalDataObjects.value[type] = {}
    }
    groomedShapesForOriginalDataObjects.value[type][id] = groomed
}

export function submitForm(action:string, payload: Record<string, any>){
    if (Object.keys(payload).every((key) => key.includes("section"))) {
        payload = Object.assign({}, ...Object.values(payload))
    }
    console.log(action, payload)
}
