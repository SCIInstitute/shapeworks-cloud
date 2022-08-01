import vtkAnnotatedCubeActor from 'vtk.js/Sources/Rendering/Core/AnnotatedCubeActor';
import { DataObject, Dataset, Subject, Particles, GroomedShape, Project } from '@/types'
import {
    getDataset,
    getGroomedShapeForDataObject, getOptimizedParticlesForDataObject,
    groomProject, optimizeProject
} from '@/api/rest';
import { ref } from '@vue/composition-api'

export const loadingState = ref<boolean>(false)

export const allDatasets = ref<Dataset[]>([])

export const selectedDataset = ref<Dataset>()

export const allProjectsForDataset = ref<Project[]>([])

export const selectedProject = ref<Project>()

export const allSubjectsForDataset = ref<Subject[]>([])

export const allDataObjectsInDataset = ref<DataObject[]>([])

export const selectedDataObjects = ref<DataObject[]>([])

export const orientationIndicator = ref<vtkAnnotatedCubeActor>(vtkAnnotatedCubeActor.newInstance())

export const particleSize = ref<number>(2)

export const particlesForOriginalDataObjects = ref<Record<string, Record<number, Particles>>>({})

export const groomedShapesForOriginalDataObjects = ref<Record<string, Record<number, GroomedShape>>>({})

export const layers = ref<Record<string, any>[]>([
    {
        name: 'Original',
        color: 'white',
        rgb: [1, 1, 1],
        available: () => true,
    },
    {
        name: 'Groomed',
        color: 'green',
        rgb: [0, 1, 0],
        available: () => {
            return Object.values(groomedShapesForOriginalDataObjects.value)
            .map((obj) => Object.values(obj).flat()).flat().length > 0
        }
    },
    {
        name: 'Reconstructed',
        color: 'red',
        rgb: [1, 0, 0],
        available: () => false,
    },
    {
        name: 'Particles',
        color: undefined,
        rgb: undefined,
        available: () => {
            return Object.values(particlesForOriginalDataObjects.value)
            .map((obj) => Object.values(obj).flat()).flat().length > 0
        }
    }
])

export const layersShown = ref<string[]>(["Original"])

export const cachedMarchingCubes = ref({})

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

export function jobAlreadyDone(action: string): Boolean {
    let layer;
    switch(action){
        case 'groom':
            layer = layers.value?.find((layer) => layer.name === 'Groomed')
            return layer ? layer.available() : false
        case 'optimize':
            layer = layers.value?.find((layer) => layer.name === 'Particles')
            return layer ? layer.available() : false
        case 'analyze':
            return false;
        default:
            return false;
    }
}

export async function spawnJob(action: string, payload: Record<string, any>): Promise<Boolean>{
    if (Object.keys(payload).every((key) => key.includes("section"))) {
        payload = Object.assign({}, ...Object.values(payload))
    }
    const projectId = selectedProject.value?.id;
    if(!projectId) return false
    switch(action){
        case 'groom':
            return (await groomProject(projectId, payload)).status === 204
        case 'optimize':
            return (await optimizeProject(projectId, payload)).status === 204
        case 'analyze':
            break;
        default:
            break;
    }
    return false;
}

export async function pollJobResults(action: string): Promise<string | undefined> {
    let resultsFound = false;
    let targetStorage = undefined;
    let testFunction: Function | undefined = undefined;
    let loadFunction: Function | undefined = undefined;
    let successFunction: Function | undefined = undefined;
    switch(action){
        case 'groom':
            targetStorage = groomedShapesForOriginalDataObjects
            testFunction = async (type: string, id: number) => {
                if(jobAlreadyDone(action)) {
                    return (await getGroomedShapeForDataObject(type, id)).filter(
                        (result: GroomedShape) => {
                            // only consider updated objects as successful results
                            return groomedShapesForOriginalDataObjects.value[type][id].modified !== result.modified
                        }
                    )
                }
                return await getGroomedShapeForDataObject(type, id)
            }
            loadFunction = loadGroomedShapeForObject
            successFunction = () => {
                cachedMarchingCubes.value = Object.fromEntries(
                    Object.entries(cachedMarchingCubes.value).filter(
                        ([cachedLabel]) => !cachedLabel.includes('Groomed')
                    )
                )
                if(!layersShown.value.includes('Groomed')) layersShown.value.push('Groomed')
            }
            break;
        case 'optimize':
            targetStorage = particlesForOriginalDataObjects
            testFunction = async (type: string, id: number) => {
                if(jobAlreadyDone(action)) {
                    return (await getOptimizedParticlesForDataObject(type, id)).filter(
                        (result: Particles) => {
                            // only consider updated objects as successful results
                            return particlesForOriginalDataObjects.value[type][id].modified !== result.modified
                        }
                    )
                }
                return await getOptimizedParticlesForDataObject(type, id)
            }
            loadFunction = loadParticlesForObject
            successFunction = () => {
                cachedMarchingCubes.value = Object.fromEntries(
                    Object.entries(cachedMarchingCubes.value).filter(
                        ([cachedLabel]) => !cachedLabel.includes('Particles')
                    )
                )
                if(!layersShown.value.includes('Particles')) layersShown.value.push('Particles')
            }
            break;
        case 'analyze':
            break;
        default:
            break;
    }
    const testObject = allDataObjectsInDataset.value[0]
    if(testObject && targetStorage && testFunction && loadFunction && successFunction) {
        resultsFound = (await testFunction(testObject.type, testObject.id)).length > 0
        if(resultsFound) {
            targetStorage.value = {}
            await Promise.all(allDataObjectsInDataset.value.map(
                (dataObject) => loadFunction ? loadFunction(dataObject.type, dataObject.id) : undefined
            ))
            if(successFunction) successFunction()
            return `Received results for ${action} job.`
        }
    } else {
        return `Error polling for ${action} results. Try refreshing the page.`
    }
    return undefined
}
