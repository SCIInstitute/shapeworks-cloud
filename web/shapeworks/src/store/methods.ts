import { AnalysisParams, CacheComparison, Project, Task } from "@/types";
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
     allDatasets,
     goodBadAngles,
     landmarkInfo,
     analysisExpandedTab,
     selectedDataObjects,
     particleSize,
     analysisFilesShown,
     meanAnalysisParticlesFiles,
     currentAnalysisParticlesFiles,
     goodBadMaxAngle,
     showDifferenceFromMeanMode,
     showGoodBadParticlesMode,
     analysisAnimate,
     allSetLandmarks,
     allSubjectsForDataset,
     constraintInfo,
     allSetConstraints,
     deepSSMResult,
     deepSSMDataTab,
} from ".";
import imageReader from "@/reader/image";
import pointsReader from "@/reader/points";
import generateMapper from "@/reader/mapper";
import constraintsReader from "@/reader/constraints";
import {
    abortTask,
    analyzeProject,
    getDataset,
    getDatasets,
    getGroomedShapeForDataObject, getOptimizedParticlesForDataObject,
    getProjectsForDataset,
    getReconstructedSamplesForProject,
    groomProject, optimizeProject, refreshProject,
    deepssmRunProject,
    getDeepSSMResultForProject,
    getDeepSSMAugPairsForProject,
    getDeepSSMTestImagesForProject,
    getDeepSSMTrainingPairsForProject,
    getDeepSSMTrainingImagesForProject,
    getTasksForProject,
    getProjectFileContents,
} from '@/api/rest';
import { layers, COLORS } from "./constants";
import { getDistance, hexToRgb } from "@/helper";
import router from "@/router";

export const resetState = () => {
    selectedDataObjects.value = [];
    layersShown.value = ['Original'];
    landmarkInfo.value = [];
    currentTasks.value = {};
    jobProgressPoll.value = undefined;
    particleSize.value = 2;
    analysis.value = undefined;
    analysisExpandedTab.value = 0;
    analysisFilesShown.value = undefined;
    currentAnalysisParticlesFiles.value = undefined;
    meanAnalysisParticlesFiles.value = undefined;
    goodBadAngles.value = undefined;
    goodBadMaxAngle.value = 45;
    showGoodBadParticlesMode.value = false;
    showDifferenceFromMeanMode.value = false;
    cachedMarchingCubes.value = {};
    cachedParticleComparisonVectors.value = {};
    cachedParticleComparisonColors.value = {};
    analysisExpandedTab.value = 0;
    analysisAnimate.value = false;
}

export const loadDataset = async (datasetId: number) => {
    // Only reload if something has changed
    if (selectedDataset.value?.id != datasetId) {
        loadingState.value = true;
        selectedDataset.value = await getDataset(datasetId);
        loadingState.value = false;
    }
}

export async function getAllDatasets() {
    const searchText = router.currentRoute.params.searchText;
    loadingState.value = true;
    allDatasets.value = (await getDatasets(searchText)).sort((a, b) => {
        if(a.created < b.created) return 1;
        if(a.created > b.created) return -1;
        return 0;
    });
    loadingState.value = false;
}

export const loadProjectForDataset = async (projectId: number) => {
    refreshProject(projectId).then((proj) => {
        if (proj.file){
            getProjectFileContents(proj.file).then((contents) => {
                proj.file_contents = contents
                selectedProject.value = proj
            })
        } else {
            selectedProject.value = proj
        }
    });
    spawnJobProgressPoll()
}

export const loadProjectsForDataset = async (datasetId: number) => {
    const searchText = router.currentRoute.params.searchText;
    loadingState.value = true;
    allProjectsForDataset.value = (await getProjectsForDataset(searchText, datasetId)).sort((a, b) => {
        if(a.created < b.created) return 1;
        if(a.created > b.created) return -1;
        return 0;
    });
    loadingState.value = false;
}

export const selectProject = (projectId: number | undefined) => {
    if (projectId) {
        resetState();
        selectedProject.value = allProjectsForDataset.value.find(
            (project: Project) => project.id == projectId,
        )
    }
}

export const loadParticlesForObject = async (type: string, id: number) => {
    let particles = await getOptimizedParticlesForDataObject(
        type, id, selectedProject.value?.id
    )
    if (particles && particles.length > 0) {
        particles = particles[0]
        if (!particlesForOriginalDataObjects.value[type]) {
            particlesForOriginalDataObjects.value[type] = {}
        }
        particlesForOriginalDataObjects.value[type][id] = particles
    } else if (
        particlesForOriginalDataObjects.value[type] &&
        particlesForOriginalDataObjects.value[type][id]
    ){
        particlesForOriginalDataObjects.value[type][id] = undefined
    }
}

export const loadGroomedShapeForObject = async (type: string, id: number) => {
    let groomed = await getGroomedShapeForDataObject(
        type, id, selectedProject.value?.id
    )
    if (groomed && groomed.length > 0) {
        groomed = groomed[0]
        if (!groomedShapesForOriginalDataObjects.value[type]) {
            groomedShapesForOriginalDataObjects.value[type] = {}
        }
        groomedShapesForOriginalDataObjects.value[type][id] = groomed
    }else if (
        groomedShapesForOriginalDataObjects.value[type] &&
        groomedShapesForOriginalDataObjects.value[type][id]
    ){
        groomedShapesForOriginalDataObjects.value[type][id] = undefined
    }
}

export const loadReconstructedSamplesForProject = async (type: string, id: number) => {
    if (selectedProject.value) {
        reconstructionsForOriginalDataObjects.value = await getReconstructedSamplesForProject(
            type, id, selectedProject.value?.id
        )
    }
}

export const loadDeepSSMDataForProject = async () => {
    if (selectedProject.value) {
        const results = await Promise.all([
            await getDeepSSMResultForProject(
                selectedProject.value.id
            ),
            await getDeepSSMAugPairsForProject(
                selectedProject.value.id
            ),
            await getDeepSSMTrainingPairsForProject(
                selectedProject.value.id
            ),
            await getDeepSSMTrainingImagesForProject(
                selectedProject.value.id
            ),
            await getDeepSSMTestImagesForProject(
                selectedProject.value.id
            )]
        )

        deepSSMResult.value = {
            result: results[0][0],
            aug_pairs: results[1],
            training_pairs: results[2],
            images: results[3],
            test_pairs: results[4]
        }
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
    const projectId = selectedProject.value?.id;
    if (!projectId) return undefined
    switch (action) {
        case 'groom':
            layersShown.value = layersShown.value.filter(
                (l) => l !== 'Groomed'
            )
            return (await groomProject(projectId, payload))?.data
        case 'optimize':
            layersShown.value = layersShown.value.filter(
                (l) => l !== 'Particles'
            )
            return (await optimizeProject(projectId, payload))?.data
        case 'analyze':
            layersShown.value = layersShown.value.filter(
                (l) => l !== 'Reconstructed'
            )
            return (await analyzeProject(projectId, payload as AnalysisParams))?.data
        case 'deepssm':
            return (await deepssmRunProject(projectId, payload))?.data
        default:
            break;
    }
    return undefined;
}

export async function spawnJobProgressPoll() {
    if (jobProgressPoll.value) clearInterval(jobProgressPoll.value)
    jobProgressPoll.value = setInterval(pollJobProgress, 1000)
}

export function pollJobProgress() {
    if (selectedProject.value) {
        const projectId = selectedProject.value.id
        getTasksForProject(projectId).then((tasks) => {
            if (tasks) {
                const refreshedTasks = {}
                tasks.forEach((task) => {
                    if (task.name && !task.abort && !task.error && task.percent_complete !== 100) {
                        refreshedTasks[`${task.name}`] = task
                    }
                })
                currentTasks.value = {
                    ...currentTasks.value,
                    ...{[projectId]: refreshedTasks}
                }
            }
        })
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
            if (analysis.value) {
                if (analysis.value.good_bad_angles) {
                    goodBadAngles.value = analysis.value.good_bad_angles
                }
            }
            break;
        case 'deepssm':
            loadFunction = loadDeepSSMDataForProject
            break;
    }
    if (layerName && loadFunction) {
        if (layerName) {
            await Promise.all(allDataObjectsInDataset.value.map(
                (dataObject) => loadFunction ? loadFunction(dataObject.type, dataObject.id) : undefined
            ))
            cachedMarchingCubes.value = Object.fromEntries(
                Object.entries(cachedMarchingCubes.value).filter(
                    ([cachedLabel]) => !cachedLabel.includes(layerName)
                )
            )
            const layer = layers.value.find((l) => l.name === layerName)
            if (layer?.available() && !layersShown.value.includes(layerName)) {
                layersShown.value = [...layersShown.value, layerName]
            }
        } else {
            loadFunction()
        }
    }
}

export async function abort(task: Task | undefined) {
    if (task && task.id) abortTask(task.id)
}

export async function switchTab(tabName: string) {
    if (!selectedProject.value) {
        return;
    }
    deepSSMDataTab.value = -1;
    const refreshedProject = await refreshProject(selectedProject.value.id)
    switch (tabName) {
        // add any other tab-switching updates here
        case 'analyze':
            if (refreshedProject) {
                analysis.value = refreshedProject.last_cached_analysis
                if (analysis.value) {
                    if (analysis.value.good_bad_angles) {
                        goodBadAngles.value = analysis.value.good_bad_angles
                    }
                }
            }
    }
}

export function calculateComparisons(mapper: any, currentPoints: number[], meanPoints: number[]) {
    const vectorValues: number[][] = []
    let colorValues: number[] = []
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

export async function cacheAllComparisons(comparisons: CacheComparison[][]) {
    if (comparisons !== undefined) {
        const cachePrep = await Promise.all(comparisons?.map(async (g) => {
            return await Promise.all(
                g.map(async (domain, i) => {
                    if(meanAnalysisParticlesFiles.value && meanAnalysisParticlesFiles.value.length > i){
                        const particleComparisonKey = domain.particles;

                        if (!cachedParticleComparisonColors.value[particleComparisonKey]) { // if the comparison is NOT already cached
                            const compareToPoints = await pointsReader(meanAnalysisParticlesFiles.value[i]);
                            const currentPoints = await pointsReader(domain.particles);

                            const currentMesh = await imageReader(domain.file, "current_mesh.vtk");

                            return {
                                "compareTo": {
                                    points: compareToPoints.getPoints().getData(),
                                    particleUrl: domain,
                                },
                                "current":  {
                                    points: currentPoints.getPoints().getData(),
                                    mapper: generateMapper(currentMesh),
                                    particleUrl: domain.particles,
                                },
                            }
                        }
                    }
                })
            )
        }))

        cachePrep.forEach((g) => {
            if (g !== undefined) {
                g.forEach((c) => {
                    if (c){
                        const { current, compareTo } = c;
                        const comparisons = calculateComparisons(current.mapper, current.points as number[], compareTo.points as number[])
                        cacheComparison(comparisons.colorValues, comparisons.vectorValues, current.particleUrl);
                    }
                })
            }
        })
    }
}


export function isShapeShown(subjectID, domain) {
    return selectedDataObjects.value.some((d) => (
        d.subject === subjectID && d.anatomy_type.replace('anatomy_', '') === domain
    ))
}

export function toggleSubjectShown(subjectID, domain) {
    const shape = allDataObjectsInDataset.value.find((d) => (
        d.subject === subjectID && d.anatomy_type.replace('anatomy_', '') === domain
    ))
    if (shape) {
        if (selectedDataObjects.value.includes(shape)) {
            selectedDataObjects.value = selectedDataObjects.value.filter(
                (s) => s !== shape
            )
        } else {
            selectedDataObjects.value = [
                ...selectedDataObjects.value,
                shape
            ]
        }
    }
}

export function getWidgetInfo(subject, item) {
    return {
        subjectName: subject.name,
        domain: item.domain,
        widgetID: item.id,
    }
}

export function getLandmarkLocation(subject, item) {
    if (
        allSetLandmarks.value &&
        allSetLandmarks.value[subject.name]
        && allSetLandmarks.value[subject.name][item.domain]
    )
    return allSetLandmarks.value[subject.name][item.domain][item.id]
}

export function setLandmarkLocation(subject, item, location) {
    if (!allSetLandmarks.value) allSetLandmarks.value = {}
    if (!allSetLandmarks.value[subject.name]) allSetLandmarks.value[subject.name] = {}
    if (!allSetLandmarks.value[subject.name][item.domain]) allSetLandmarks.value[subject.name][item.domain] = {}
    allSetLandmarks.value[subject.name][item.domain][item.id] = location
}


export function reassignLandmarkIDsByIndex() {
    const reassignedIds = {}
    landmarkInfo.value = landmarkInfo.value.map((info, index) => {
        if (info.id !== undefined) reassignedIds[info.id] = index
        return Object.assign(info, {id: index})
    })
    if (allSetLandmarks.value) {
        allSetLandmarks.value = Object.fromEntries(
            Object.entries(allSetLandmarks.value)
            .map(([subjectName, subjectRecords]) => {
                return [subjectName, Object.fromEntries(
                    Object.entries(subjectRecords).map(([domain, domainRecords]) => {
                        domainRecords = Object.fromEntries(
                            Object.entries(domainRecords)
                            .filter(([lId,]) => Object.keys(reassignedIds).includes(lId))
                            .map(([lId, lData]) => {
                                return [reassignedIds[lId], lData]
                            })
                        )
                        return [domain, domainRecords]
                    })
                )]
            })
        )
    }
}

export function reassignLandmarkNumSetValues() {
    // only reassign if a value has changed
    const reassign = false
    const newInfo = landmarkInfo.value.map((lInfo) => {
        const newNumSet = allSubjectsForDataset.value.filter((s) => !!getLandmarkLocation(s, lInfo)).length
        if (newNumSet != lInfo.num_set) {
            lInfo.num_set = newNumSet
        }
        return lInfo
    })
    if (reassign) landmarkInfo.value = newInfo
}


export async function getLandmarks() {
    allSetLandmarks.value = {}
    if(selectedProject.value?.landmarks) {
        landmarkInfo.value = selectedProject.value.landmarks_info.map((lInfo, index) => {
            if (!lInfo.id) {
                lInfo.id = index
            }
            if (!lInfo.name) {
                lInfo.name = `L${index}`
            }
            if (!lInfo.color) {
                lInfo.color = COLORS[index % COLORS.length]
            }
            if (lInfo.color.toString().includes('#')) {
                lInfo.color = hexToRgb(lInfo.color.toString())
            }
            lInfo.num_set = 0
            return lInfo
        })

        for (let i = 0; i < selectedProject.value.landmarks.length; i++) {
            const landmarksObject = selectedProject.value.landmarks[i]
            const subject = allSubjectsForDataset.value.find((s) => s.id === landmarksObject.subject)
            const pointData = await pointsReader(landmarksObject.file)
            const locationData = pointData.getPoints().getData()
            const locations: number[][] = []
            for (let p = 0; p < locationData.length; p+=3) {
                const location = locationData.slice(p, p+3) as number[]
                locations.push(location)
            }
            const lInfos = landmarkInfo.value.filter((lInfo) => lInfo.domain === landmarksObject.anatomy_type.replace('anatomy_', ''))
            locations.forEach((location, index) => {
                const lInfo = lInfos[index]
                setLandmarkLocation(subject, lInfo, location)
            })
        }
        // reassign store var for listeners
        allSetLandmarks.value = Object.assign({}, allSetLandmarks.value)
        reassignLandmarkNumSetValues();
    }
}

export function getConstraintLocation(subject, item) {
    if (
        allSetConstraints.value &&
        allSetConstraints.value[subject.name]
        && allSetConstraints.value[subject.name][item.domain]
    )
    return allSetConstraints.value[subject.name][item.domain][item.id]
}

export function setConstraintLocation(subject, item, location) {
    if (!allSetConstraints.value) allSetConstraints.value = {}
    if (!allSetConstraints.value[subject.name]) allSetConstraints.value[subject.name] = {}
    if (!allSetConstraints.value[subject.name][item.domain]) allSetConstraints.value[subject.name][item.domain] = {}
    allSetConstraints.value[subject.name][item.domain][item.id] = location
    allSetConstraints.value = Object.assign({}, allSetConstraints.value)
    reassignConstraintNumSetValues()
}


export function reassignConstraintIDsByIndex() {
    const reassignedIds = {}
    constraintInfo.value = constraintInfo.value.map((info, index) => {
        if (info.id !== undefined) reassignedIds[info.id] = index
        return Object.assign(info, {id: index})
    })
    if (allSetConstraints.value) {
        allSetConstraints.value = Object.fromEntries(
            Object.entries(allSetConstraints.value)
            .map(([subjectName, subjectRecords]) => {
                return [subjectName, Object.fromEntries(
                    Object.entries(subjectRecords).map(([domain, domainRecords]) => {
                        domainRecords = Object.fromEntries(
                            Object.entries(domainRecords)
                            .filter(([cId,]) => Object.keys(reassignedIds).includes(cId))
                            .map(([cId, cData]) => {
                                return [reassignedIds[cId], cData]
                            })
                        )
                        return [domain, domainRecords]
                    })
                )]
            })
        )
    }
}

export function reassignConstraintNumSetValues() {
    // only reassign if a value has changed
    const reassign = false
    const newInfo = constraintInfo.value.map((cInfo) => {
        const newNumSet = allSubjectsForDataset.value.filter((s) => !!getConstraintLocation(s, cInfo)).length
        if (newNumSet != cInfo.num_set) {
            cInfo.num_set = newNumSet
        }
        return cInfo
    })
    if (reassign) constraintInfo.value = newInfo
}

export async function getConstraints() {
    allSetConstraints.value = {}
    constraintInfo.value = []
    if(selectedProject.value?.constraints) {
        for (let i = 0; i < selectedProject.value.constraints.length; i++) {
            const constraintsObject = selectedProject.value.constraints[i]
            const subject = allSubjectsForDataset.value.find((s) => s.id === constraintsObject.subject)
            const domain = constraintsObject.anatomy_type?.replace('anatomy_', '') || '0'
            if (subject) {
                const constraintsData = await constraintsReader(constraintsObject.file);
                ['plane', 'paint'].forEach((constraintType) => {
                    const newConstraintsOfType = constraintsData.filter((cData) => cData.type === constraintType)
                    const existingConstraintsOfType = constraintInfo.value.filter((cData) => cData.type === constraintType && cData.domain === domain)
                    for(let i=0; i<newConstraintsOfType.length; i++) {
                        let cInfo;
                        const cData = newConstraintsOfType[i]
                        if (i >= existingConstraintsOfType.length) {
                            cInfo = {
                                id: constraintInfo.value.length,
                                type: constraintType,
                                name: cData.name,
                                domain
                            }
                            constraintInfo.value.push(cInfo)
                        } else {
                            cInfo = existingConstraintsOfType[i]
                        }
                        if(cInfo) setConstraintLocation(subject, cInfo, cData)
                    }
                })
            }
        }
        // reassign store var for listeners
        allSetConstraints.value = Object.assign({}, allSetConstraints.value)
        reassignConstraintNumSetValues();
    }
}
