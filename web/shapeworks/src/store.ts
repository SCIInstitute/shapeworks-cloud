import vtkAnnotatedCubeActor from 'vtk.js/Sources/Rendering/Core/AnnotatedCubeActor';
import {
    DataObject, Dataset, Subject,
    Particles, GroomedShape, Project,
    ReconstructedSample, VTKInstance,
    Analysis, Task
} from '@/types'
import {
    abortTask,
    deleteTaskProgress,
    getDataset,
    getGroomedShapeForDataObject, getOptimizedParticlesForDataObject,
    getProjectsForDataset,
    getReconstructedSamplesForProject,
    groomProject, optimizeProject, refreshProject
} from '@/api/rest';
import { ref } from '@vue/composition-api'
import { getTaskProgress } from '@/api/rest';


export const loadingState = ref<boolean>(false)

export const currentError = ref<string>()

export const vtkInstance = ref<VTKInstance>()

export const allDatasets = ref<Dataset[]>([])

export const selectedDataset = ref<Dataset>()

export const allProjectsForDataset = ref<Project[]>([])

export const selectedProject = ref<Project>()

export const allSubjectsForDataset = ref<Subject[]>([])

export const allDataObjectsInDataset = ref<DataObject[]>([])

export const selectedDataObjects = ref<DataObject[]>([])

export const orientationIndicator = ref<vtkAnnotatedCubeActor>(vtkAnnotatedCubeActor.newInstance())

export const particleSize = ref<number>(2)

export const reconstructionsForOriginalDataObjects = ref<ReconstructedSample[]>([])

export const particlesForOriginalDataObjects = ref<Record<string, Record<number, Particles>>>({})

export const groomedShapesForOriginalDataObjects = ref<Record<string, Record<number, GroomedShape>>>({})

export const analysis = ref<Analysis>();

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
        available: () => {
            return reconstructionsForOriginalDataObjects.value?.length > 0
        },
    },
    {
        name: 'Particles',
        color: undefined,
        rgb: undefined,
        available: () => {
            return Object.values(particlesForOriginalDataObjects.value)
            .map((obj) => Object.values(obj).flat()).flat().length > 0
        }
    },
    {
        name: 'Landmarks',
        color: undefined,
        rgb: undefined,
        available: () => {
            return selectedProject.value?.landmarks && selectedProject.value.landmarks.length > 0
        }
    }
])

export const layersShown = ref<string[]>(["Original"])

export const showDifferenceFromMeanMode = ref<Boolean>(false);

export const analysisFileShown = ref<string>();

export const currentAnalysisFileParticles = ref<string>();

export const meanAnalysisFileParticles = ref<string>();

export const cachedMarchingCubes = ref({})

export const cachedParticleComparisonVectors = ref({})

export const cachedParticleComparisonColors = ref({})

export const vtkShapesByType = ref<Record<string, any[]>>({
    "Original": [],
    "Groomed": [],
    "Reconstructed": [],
    "Particles": []
})

export const currentTasks = ref<Record<number, Record<string, Task| undefined>>>({})

export const jobProgressPoll = ref();

export const loadDataset = async (datasetId: number) => {
    // Only reload if something has changed
    if (selectedDataset.value?.id != datasetId) {
        loadingState.value = true;
        selectedDataset.value = await getDataset(datasetId);
        loadingState.value = false;
    }
}

export const loadProjectForDataset = async (projectId: number|undefined, datasetId: number) => {
    allProjectsForDataset.value = await getProjectsForDataset(datasetId);
    if(projectId) {
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
    if(!particlesForOriginalDataObjects.value[type]){
        particlesForOriginalDataObjects.value[type] = {}
    }
    particlesForOriginalDataObjects.value[type][id] = particles
}

export const loadGroomedShapeForObject = async (type: string, id: number) => {
    let groomed = await getGroomedShapeForDataObject(
        type, id, selectedProject.value?.id
    )
    if (groomed.length > 0) groomed = groomed[0]
    if(!groomedShapesForOriginalDataObjects.value[type]){
        groomedShapesForOriginalDataObjects.value[type] = {}
    }
    groomedShapesForOriginalDataObjects.value[type][id] = groomed
}

export const loadReconstructedSamplesForProject = async (type: string, id: number) => {
    if (selectedProject.value){
        reconstructionsForOriginalDataObjects.value = await getReconstructedSamplesForProject(
            type, id, selectedProject.value?.id
        )
    }
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

export async function spawnJob(action: string, payload: Record<string, any>): Promise<any>{
    if (Object.keys(payload).every((key) => key.includes("section"))) {
        payload = Object.assign({}, ...Object.values(payload))
    }
    const projectId = selectedProject.value?.id;
    if(!projectId) return undefined
    switch(action){
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

export async function pollJobProgress(){
    if(selectedProject.value && currentTasks.value[selectedProject.value.id]){
        const refreshedTasks = await Promise.all(
            Object.entries(currentTasks.value[selectedProject.value.id])
            .map(async ([taskName, task]) => {
                if (task?.id){
                    task = await getTaskProgress(task.id)
                    if (task?.id && task?.percent_complete === 100) {
                        await deleteTaskProgress(task?.id)
                        task.id = undefined
                        setTimeout(() => {
                            if (selectedProject.value){
                                currentTasks.value[selectedProject.value.id][taskName] = undefined
                            }
                        }, 1000)
                        fetchJobResults(taskName.replace('_task', ''))
                    }
                }
                return [taskName, task]
            }))
        currentTasks.value[selectedProject.value.id] = Object.fromEntries(refreshedTasks)
        currentTasks.value = {...currentTasks.value}  // reassign for watch response
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
    if(!selectedProject.value) {
        return;
    }
    const refreshedProject = await refreshProject(selectedProject.value.id)
    let layerName: string = ''
    let loadFunction: Function | undefined = undefined
    switch(taskName) {
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
        if(!layersShown.value.includes(layerName)) layersShown.value.push(layerName)
    }
}

export async function abort(task: Task) {
    if(task.id) abortTask(task.id)
    if (selectedProject.value) {
        currentTasks.value[selectedProject.value.id] = {}
    }
    clearInterval(jobProgressPoll.value)
    jobProgressPoll.value = undefined
}

export async function switchTab(tabName: string){
    if(!selectedProject.value) {
        return;
    }
    const refreshedProject = await refreshProject(selectedProject.value.id)
    switch(tabName) {
        // add any other tab-switching updates here
        case 'analyze':
            if (refreshedProject && !currentTasks.value[selectedProject.value.id]) {
                analysis.value = refreshedProject.last_cached_analysis
            }
    }
}
