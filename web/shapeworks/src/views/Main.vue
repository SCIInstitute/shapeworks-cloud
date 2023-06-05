<script lang="ts">
import {
    defineComponent, onMounted, ref,
    watch, computed, nextTick,
    onBeforeUnmount,
} from 'vue';
import _ from 'lodash';
import imageReader from '../reader/image';
import pointsReader from '../reader/points';
import { groupBy, shortFileName } from '../helper';
import { DataObject, ShapeData } from '@/types';
import ShapeViewer from '../components/ShapeViewer/viewer.vue';
import DataList from '../components/DataList.vue'
import RenderControls from '../components/RenderControls.vue'
import {
    selectedDataset,
    allSubjectsForDataset,
    selectedDataObjects,
    loadDataset,
    particleSize,
    particlesForOriginalDataObjects,
    layersShown,
    groomedShapesForOriginalDataObjects,
    selectedProject,
    loadProjectForDataset,
    reconstructionsForOriginalDataObjects,
    analysisFileShown,
    meanAnalysisFileParticles,
    currentAnalysisFileParticles,
    switchTab,
    landmarkColorList,
    jobAlreadyDone,
    analysisExpandedTab,
allProjectsForDataset,
loadProjectsForDataset,
} from '@/store';
import router from '@/router';
import TabForm from '@/components/TabForm.vue';
import AnalysisTab from '@/components/Analysis/AnalysisTab.vue';
import InfoTab from '@/components/InfoTab.vue';


export default defineComponent({
    components: {
        ShapeViewer,
        DataList,
        RenderControls,
        TabForm,
        AnalysisTab,
        InfoTab,
    },
    props: {
        dataset: {
            type: Number,
            required: true,
        },
        project: {
            type: Number,
            required: true,
        }
    },
    setup(props) {
        const drawerWidth = ref<number>(600);
        const drawer = ref();
        const renderAreaStyle = computed(() => {
            let width = `calc(100% - ${drawerWidth.value}px)`
            return {
                width,
                position: 'absolute',
                left: `${drawerWidth.value}px`,
                top: '70px',
                height: 'calc(100% - 70px)'
            }
        })

        const tab = ref();
        const rows = ref<number>(1);
        const cols = ref<number>(1);
        const renderData = ref<Record<string, ShapeData[]>>({});
        const renderMetaData = ref<Record<string, ShapeData>>({});

        onMounted(async () => {
            try {
                await loadDataset(props.dataset);
                await loadProjectForDataset(props.project);
            } catch(e) {
                console.log(e);
                toSelectPage();
            }
            nextTick(() => {
                window.addEventListener('resize', onResize);
            })
        })

        onBeforeUnmount(() => {
            window.removeEventListener('resize', onResize);
        })

        function onResize() {
            refreshRender()
        }

        async function toSelectPage() {
            selectedProject.value = undefined;
            analysisFileShown.value = undefined;
            if (allProjectsForDataset.value.length === 0 && selectedDataset.value) {
                loadProjectsForDataset(selectedDataset.value.id);
            }
            router.push('/dataset/'+selectedDataset.value?.id);
        }

        function prepareDrawer() {
            if (drawer.value && drawer.value.$el) {
                let i = drawer.value.$el.querySelector(
                    ".v-navigation-drawer__border"
                );
                i.style.width = "10px";
                i.style.cursor = "ew-resize";
                i.addEventListener(
                    "mousedown",
                    function(e: MouseEvent) {
                        e.preventDefault()
                        if (e.offsetX < 300) {
                            drawer.value.$el.style.transition ='initial';
                            document.addEventListener("mousemove", setDrawerWidth, false);
                        }
                    },
                    false
                );
                document.addEventListener(
                    "mouseup",
                    function() {
                        drawer.value.$el.style.transition ='';
                        document.body.style.cursor = "";
                        document.removeEventListener("mousemove", setDrawerWidth, false);
                    },
                    false
                );
            }
        }

        function setDrawerWidth(e: MouseEvent) {
            document.body.style.cursor = "ew-resize";
            drawer.value.$el.style.width =  e.clientX + "px";
            drawerWidth.value = e.clientX
        }

        async function refreshRender() {
            let newRenderData = {}
            renderMetaData.value = {}
            const groupedSelections: Record<string, DataObject[]> = groupBy(selectedDataObjects.value, 'subject')
            if (analysisFileShown.value) {
                const currParticles = await pointsReader(
                    currentAnalysisFileParticles.value
                )
                const meanParticles = await pointsReader(
                    meanAnalysisFileParticles.value
                )
                renderMetaData.value = {
                    "mean": {
                        shape: await imageReader(undefined),
                        points: meanParticles,
                    },
                    "current": {
                        shape: await imageReader(undefined),
                        points: currParticles,
                    }
                }
                newRenderData =
                    (analysisExpandedTab.value === 0) ?
                    {
                        "PCA": [{
                            shape: await imageReader(
                                analysisFileShown.value,
                                shortFileName(analysisFileShown.value),
                            ),
                            points: await pointsReader(
                                currentAnalysisFileParticles.value
                            )
                        }]
                    }:
                    {
                        "GROUP": [{
                            shape: await imageReader(
                                analysisFileShown.value,
                                shortFileName(analysisFileShown.value),
                            ),
                            points: await pointsReader(
                                currentAnalysisFileParticles.value
                            )
                        }]
                    }
            } else {
                newRenderData = Object.fromEntries(
                    await Promise.all(Object.entries(groupedSelections).map(
                        async ([subjectId, dataObjects]) => {
                            let subjectName = subjectId;
                            if(allSubjectsForDataset.value){
                                const subject = allSubjectsForDataset.value.find(
                                    (subject) => subject.id.toString() === subjectId
                                )
                                if (subject) subjectName = subject.name
                            }
                            const shapeDatas = (await Promise.all(dataObjects.map(
                                (dataObject) => {
                                    const shapePromises = [];
                                    if(layersShown.value.includes("Original")){
                                      shapePromises.push(
                                        imageReader(
                                            dataObject.file,
                                            shortFileName(dataObject.file),
                                        )
                                      )
                                    }
                                    if(layersShown.value.includes("Groomed")){
                                        const shapeURL = groomedShapesForOriginalDataObjects.value[
                                            dataObject.type
                                        ][dataObject.id].file
                                        shapePromises.push(
                                          imageReader(
                                            shapeURL,
                                            shortFileName(shapeURL),
                                            "Groomed",
                                        )
                                      )
                                    }
                                    if(layersShown.value.includes("Reconstructed")){
                                        const targetReconstruction = reconstructionsForOriginalDataObjects.value.find(
                                            (reconstructed) => {
                                                const particles = reconstructed.particles
                                                let originalId;
                                                if(dataObject.type === 'mesh'){
                                                    originalId = particles.groomed_mesh.mesh
                                                } else if (dataObject.type === 'segmentation'){
                                                    originalId = particles.groomed_segmentation.segmentation
                                                }
                                                return originalId === dataObject.id
                                            }
                                        )
                                        if (targetReconstruction) {
                                            const shapeURL = targetReconstruction.file
                                            shapePromises.push(
                                                imageReader(
                                                    shapeURL,
                                                    shortFileName(shapeURL),
                                                    "Reconstructed"
                                                )
                                            )
                                        }
                                    }

                                    let particleURL;
                                    if(layersShown.value.includes("Particles")){
                                        particleURL = particlesForOriginalDataObjects.value[dataObject.type][dataObject.id]?.local
                                    }

                                    let landmarksURL;
                                    if(layersShown.value.includes("Landmarks")) {
                                        landmarksURL = selectedProject.value?.landmarks?.find(
                                            (l) => l.subject.toString() === subjectId
                                        )?.file
                                    }

                                    return Promise.all([
                                        Promise.all(shapePromises),
                                        pointsReader(particleURL),
                                        pointsReader(landmarksURL)
                                    ])
                                }
                            )))
                            .map(([imageData, particleData, landmarkData]) => (
                                {shape: imageData, points: particleData, landmarks: landmarkData}
                            ))
                            return [
                                subjectName, shapeDatas
                            ]
                        }
                    )
                ))
            }

            const n = Object.keys(newRenderData).length;
            const sqrt = Math.ceil(Math.sqrt(n));
            const numGroups = Math.min(sqrt, 5)
            const renderAreaWidth = window.innerWidth - drawerWidth.value
            const renderAreaHeight = window.innerHeight - 120
            const renderAreaRatio = renderAreaWidth / renderAreaHeight
            if (renderAreaRatio > 1) {
                rows.value = Math.ceil(n / numGroups);
                cols.value = numGroups;
            } else {
                cols.value = Math.ceil(n / numGroups);
                rows.value = numGroups;
            }
            renderData.value = newRenderData
        }

        const debouncedRefreshRender = _.debounce(refreshRender, 300)

        watch(drawer, prepareDrawer)
        watch(selectedDataObjects, debouncedRefreshRender)
        watch(layersShown, debouncedRefreshRender)
        watch(analysisFileShown, debouncedRefreshRender)
        watch(landmarkColorList, debouncedRefreshRender)
        watch(meanAnalysisFileParticles, debouncedRefreshRender)
        watch(tab, switchTab)

        return {
            drawer,
            drawerWidth,
            setDrawerWidth,
            renderAreaStyle,
            tab,
            rows,
            cols,
            renderData,
            renderMetaData,
            selectedDataset,
            selectedProject,
            selectedDataObjects,
            toSelectPage,
            refreshRender,
            jobAlreadyDone,
            particleSize,
            analysisFileShown,
        }
    }
})
</script>


<template>
    <div class='content-area' style='height: 100%' v-if="selectedDataset">
        <v-navigation-drawer
            ref="drawer"
            :width="drawerWidth"
            permanent
            absolute
        >
                <v-list-item>
                    <v-list-item-title class="text-h6">
                        <v-tooltip bottom>
                        <template v-slot:activator="{ on, attrs }">
                            <v-icon
                            dark
                            v-bind="attrs"
                            v-on="on"
                            @click="toSelectPage"
                            >
                            mdi-arrow-left
                            </v-icon>
                        </template>
                        <span>Return to dataset/project selection</span>
                        </v-tooltip>
                        Dataset: {{ selectedDataset.name }}
                    </v-list-item-title>
                </v-list-item>
                <v-list-item>
                    <v-icon />
                    <v-tabs v-model="tab" fixed-tabs>
                        <v-tab href="#data">Data</v-tab>
                        <v-tab-item value="data">
                            <data-list :dataset="dataset" autoSelectOne/>
                        </v-tab-item>
                        <v-tab href="#info">Info</v-tab>
                        <v-tab-item value="info">
                            <info-tab />
                        </v-tab-item>
                        <v-tab href="#groom">Groom</v-tab>
                        <v-tab-item value="groom">
                            <span
                                v-if="selectedProject && selectedProject.readonly"
                                class="red--text pa-3"
                            >
                                This project is read only.
                                No grooming or optimizing may be performed.
                            </span>
                            <tab-form v-else form="groom" @change="refreshRender"/>
                        </v-tab-item>
                        <v-tab href="#optimize">Optimize</v-tab>
                        <v-tab-item value="optimize">
                            <span
                                v-if="selectedProject && selectedProject.readonly"
                                class="red--text pa-3"
                            >
                                This project is read only.
                                No grooming or optimizing may be performed.
                            </span>
                            <tab-form
                                v-else
                                form="optimize"
                                @change="refreshRender"
                                :prerequisite="() => jobAlreadyDone('groom')"
                                prerequisite_unfulfilled="Perform a groom operation before optimizing."
                            />
                        </v-tab-item>
                        <v-tab href="#analyze">Analyze</v-tab>
                        <v-tab-item value="analyze">
                            <analysis-tab @change="refreshRender" :currentTab="tab || ''"/>
                        </v-tab-item>
                    </v-tabs>
                </v-list-item>
                <br>
        </v-navigation-drawer>
        <v-card :style="renderAreaStyle" class="px-3 render-controls">
            <render-controls @change="refreshRender" :currentTab="tab || ''"/>
        </v-card>

        <div :style="renderAreaStyle" class="render-area pa-3">
            <template v-if="selectedDataObjects.length > 0 || analysisFileShown">
                <shape-viewer
                    :data="renderData"
                    :metaData="renderMetaData"
                    :rows="rows"
                    :columns="cols"
                    :glyph-size="particleSize"
                    :currentTab="tab || ''"
                    :drawerWidth="drawerWidth"
                />
            </template>
            <span v-else>Select any number of data objects</span>
        </div>
    </div>
</template>

<style>
.content-area {
    position: relative;
    min-height: calc(100vh - 160px);
    background-color: #1e1e1e;
}
.render-controls {
    height: 70px!important;
    top: 0!important;
    z-index: 2;
}
</style>
