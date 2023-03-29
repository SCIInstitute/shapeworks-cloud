<script lang="ts">
import {
    defineComponent, onMounted, ref,
    watch, computed, nextTick,
    onBeforeUnmount,
} from '@vue/composition-api';
import _ from 'lodash';
import imageReader from '../reader/image';
import pointsReader from '../reader/points';
import { groupBy, shortFileName } from '../helper';
import { DataObject, ShapeData } from '@/types';
import ShapeViewer from '../components/ShapeViewer.vue';
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
    switchTab
} from '../store';
import router from '@/router';
import TabForm from '@/components/TabForm.vue';
import { jobAlreadyDone } from '../store';
import AnalysisTab from '@/components/AnalysisTab.vue';


export default defineComponent({
    components: {
        ShapeViewer,
        DataList,
        RenderControls,
        TabForm,
        AnalysisTab,
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
                await loadProjectForDataset(props.project, props.dataset);
            } catch(e) {
                router.push({
                    name: 'select'
                })
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
            router.push({
                name: 'select',
            });
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
                newRenderData = {
                    "PCA": [{
                        shape: await imageReader(
                            analysisFileShown.value,
                            shortFileName(analysisFileShown.value),
                        ),
                        points: await pointsReader(undefined)
                    }
                    ]
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
                                    return Promise.all([
                                        Promise.all(shapePromises),
                                        pointsReader(particleURL)
                                    ])
                                }
                            )))
                            .map(([imageData, particleData]) => ({shape: imageData, points: particleData}))
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
                            <data-list :dataset="dataset"/>
                        </v-tab-item>
                        <v-tab href="#groom">Groom</v-tab>
                        <v-tab-item value="groom">
                            <tab-form form="groom" @change="refreshRender"/>
                        </v-tab-item>
                        <v-tab href="#optimize">Optimize</v-tab>
                        <v-tab-item value="optimize">
                            <tab-form
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
