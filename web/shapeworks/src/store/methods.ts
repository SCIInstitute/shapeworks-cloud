import { Project, Task } from "@/types";
import {
     loadingState,
     selectedDataset,
     selectedProject,
     allProjectsForDataset,
     layersShown,
     particlesForOriginalDataObjects,
     allDataObjectsInDataset,
     analysis,
     cachedMarchingCubes,
     currentTasks,
     groomedShapesForOriginalDataObjects,
     jobProgressPoll,
     reconstructionsForOriginalDataObjects,
     cachedParticleComparisonColors,
     cachedParticleComparisonVectors,
} from ".";
import {
    abortTask,
    deleteTaskProgress,
    getDataset,
    getGroomedShapeForDataObject, getOptimizedParticlesForDataObject,
    getProjectsForDataset,
    getReconstructedSamplesForProject,
    getTaskProgress,
    groomProject, optimizeProject, refreshProject
} from '@/api/rest';
import { layers } from "./constants";
import { getDistance } from "@/helper";
import { TypedArray } from "vtk.js/Sources/types";

export const loadDataset = async (datasetId: number) => {
    // Only reload if something has changed
    if (selectedDataset.value?.id != datasetId) {
        loadingState.value = true;
        selectedDataset.value = await getDataset(datasetId);
        loadingState.value = false;
    }
}

export const loadProjectForDataset = async (projectId: number | undefined, datasetId: number) => {
    allProjectsForDataset.value = await getProjectsForDataset(datasetId);
    if (projectId) {
        selectedProject.value = allProjectsForDataset.value.find(
            (project: Project) => project.id == projectId,
        )
        layersShown.value = ["Original"]
    }
}

export const loadParticlesForObject = async (type: string, id: number) => {
    let particles = await getOptimizedParticlesForDataObject(
        type, id, selectedProject.value?.id
    )
    if (particles.length > 0) particles = particles[0]
    if (!particlesForOriginalDataObjects.value[type]) {
        particlesForOriginalDataObjects.value[type] = {}
    }
    particlesForOriginalDataObjects.value[type][id] = particles
}

export const loadGroomedShapeForObject = async (type: string, id: number) => {
    let groomed = await getGroomedShapeForDataObject(
        type, id, selectedProject.value?.id
    )
    if (groomed.length > 0) groomed = groomed[0]
    if (!groomedShapesForOriginalDataObjects.value[type]) {
        groomedShapesForOriginalDataObjects.value[type] = {}
    }
    groomedShapesForOriginalDataObjects.value[type][id] = groomed
}

export const loadReconstructedSamplesForProject = async (type: string, id: number) => {
    if (selectedProject.value) {
        reconstructionsForOriginalDataObjects.value = await getReconstructedSamplesForProject(
            type, id, selectedProject.value?.id
        )
    }
}


export function jobAlreadyDone(action: string): Boolean {
    let layer;
    switch (action) {
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

export async function spawnJob(action: string, payload: Record<string, any>): Promise<any> {
    if (Object.keys(payload).every((key) => key.includes("section"))) {
        payload = Object.assign({}, ...Object.values(payload))
    }
    const projectId = selectedProject.value?.id;
    if (!projectId) return undefined
    switch (action) {
        case 'groom':
            return (await groomProject(projectId, payload))?.data
        case 'optimize':
            return (await optimizeProject(projectId, payload))?.data
        default:
            break;
    }
    return undefined;
}

export async function spawnJobProgressPoll() {
    jobProgressPoll.value = setInterval(pollJobProgress, 1000)
}

export async function pollJobProgress() {
    if (selectedProject.value && currentTasks.value[selectedProject.value.id]) {
        const refreshedTasks = await Promise.all(
            Object.entries(currentTasks.value[selectedProject.value.id])
                .map(async ([taskName, task]) => {
                    if (task?.id) {
                        task = await getTaskProgress(task.id)
                        if (task?.id && task?.percent_complete === 100) {
                            await deleteTaskProgress(task?.id)
                            task.id = undefined
                            setTimeout(() => {
                                if (selectedProject.value) {
                                    currentTasks.value[selectedProject.value.id][taskName] = undefined
                                }
                            }, 1000)
                            fetchJobResults(taskName.replace('_task', ''))
                        }
                    }
                    return [taskName, task]
                }))
        currentTasks.value[selectedProject.value.id] = Object.fromEntries(refreshedTasks)
        currentTasks.value = { ...currentTasks.value }  // reassign for watch response
        if (
            Object.values(currentTasks.value[selectedProject.value.id])
                .every(task => task?.id === undefined)
        ) {
            clearInterval(jobProgressPoll.value)
            jobProgressPoll.value = undefined
        }
    }
}

export async function fetchJobResults(taskName: string) {
    if (!selectedProject.value) {
        return;
    }
    const refreshedProject = await refreshProject(selectedProject.value.id)
    let layerName: string = ''
    let loadFunction: Function | undefined = undefined
    switch (taskName) {
        case 'groom':
            layerName = 'Groomed'
            loadFunction = loadGroomedShapeForObject
            break;
        case 'optimize':
            layerName = 'Particles'
            loadFunction = loadParticlesForObject
            break;
        case 'analyze':
            layerName = 'Reconstructed'
            loadFunction = loadReconstructedSamplesForProject
            analysis.value = refreshedProject?.last_cached_analysis
            break;
    }
    if (layerName && loadFunction) {
        await Promise.all(allDataObjectsInDataset.value.map(
            (dataObject) => loadFunction ? loadFunction(dataObject.type, dataObject.id) : undefined
        ))
        cachedMarchingCubes.value = Object.fromEntries(
            Object.entries(cachedMarchingCubes.value).filter(
                ([cachedLabel]) => !cachedLabel.includes(layerName)
            )
        )
        if (!layersShown.value.includes(layerName)) layersShown.value.push(layerName)
    }
}

export async function abort(task: Task) {
    if (task.id) abortTask(task.id)
    if (selectedProject.value) {
        currentTasks.value[selectedProject.value.id] = {}
    }
    clearInterval(jobProgressPoll.value)
    jobProgressPoll.value = undefined
}

export async function switchTab(tabName: string) {
    if (!selectedProject.value) {
        return;
    }
    const refreshedProject = await refreshProject(selectedProject.value.id)
    switch (tabName) {
        // add any other tab-switching updates here
        case 'analyze':
            if (refreshedProject && !currentTasks.value[selectedProject.value.id]) {
                analysis.value = refreshedProject.last_cached_analysis
            }
    }
}


export function calculateComparisons(mapper: any, currentPoints: TypedArray, meanPoints: TypedArray) {
    const vectorValues: number[][] = []
    let colorValues = []
    for (let i = 0; i < currentPoints.length; i += 3){
        const currentParticle = currentPoints.slice(i, i+3)
        const meanParticle = meanPoints.slice(i, i+3)
        const distance = getDistance(currentParticle as number[], meanParticle as number[], true)
        vectorValues.push([...currentParticle, distance])
    }

    const pointLocations = mapper.getInputData().getPoints().getData()
    const normals = mapper.getInputData().getPointData().getArrayByName('Normals').getData()
    colorValues = Array.from(
        [...Array(pointLocations.length / 3).keys()].map(
        (i) =>  {
            let colorVal = 0;
            const location = pointLocations.slice(i * 3, i * 3 + 3)
            const normal = normals.slice(i * 3, i * 3 + 3)
            const nearbyParticles = vectorValues.map(
            (p, i) => [getDistance(p.slice(0, 3), location), i, ...p]
            ).sort((a, b) => a[0] - b[0]).slice(0, 10)
            const nearestParticleIndex = nearbyParticles[0][1]
            if (vectorValues[nearestParticleIndex].length < 5){
            vectorValues[nearestParticleIndex].push(...normal)
            }
            colorVal = nearbyParticles[0][5]
            nearbyParticles.slice(1).forEach((p) => {
            const weight = 1 / p[0];
            colorVal = (colorVal * (1 - weight)) + (p[5] * weight)
            })
            return colorVal/10 + 0.5
        }
        )
    )

    return { colorValues: colorValues, vectorValues: vectorValues }
}

export function cacheComparison(colorValues: number[], vectorValues: number[][], particleComparisonKey: string) {
    cachedParticleComparisonColors.value[particleComparisonKey] = colorValues
    cachedParticleComparisonVectors.value[particleComparisonKey] = vectorValues
}
