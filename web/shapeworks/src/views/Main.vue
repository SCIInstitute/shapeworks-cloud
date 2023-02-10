<script lang="ts">
import _ from 'lodash';
import imageReader from '../reader/image';
import pointsReader from '../reader/points';
import { groupBy, shortFileName } from '../helper';
import { defineComponent, onMounted, ref, watch } from '@vue/composition-api';
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
        const mini = ref(false);
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
        })

        async function toSelectPage() {
            selectedProject.value = undefined;
            analysisFileShown.value = undefined;
            router.push({
                name: 'select',
            });
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
            if(sqrt <= 5) {
                rows.value = Math.ceil(n / sqrt);
                cols.value = sqrt;
            } else {
                rows.value = Math.ceil(n / 5);
                cols.value = 5;
            }
            renderData.value = newRenderData
        }

        const debouncedRefreshRender = _.debounce(refreshRender, 300)


        watch(selectedDataObjects, debouncedRefreshRender)
        watch(layersShown, debouncedRefreshRender)
        watch(analysisFileShown, debouncedRefreshRender)
        watch(tab, switchTab)

        return {
            mini,
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
        <v-navigation-drawer :mini-variant.sync="mini" width="650" permanent absolute>
                <v-list-item>
                    <v-btn
                        icon
                        @click.stop="mini=!mini"
                        class="mr-3"
                    >
                        <v-icon large>mdi-menu</v-icon>
                    </v-btn>
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
                    <v-btn
                        icon
                        @click.stop="mini=!mini"
                        class="pr-3"
                    >
                        <v-icon large>mdi-chevron-left</v-icon>
                    </v-btn>
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
        <v-card
            :class="mini ?'px-5 width-change maximize' :'width-change px-5'"
        >
            <render-controls @change="refreshRender" :currentTab="tab || ''"/>
        </v-card>

        <div :class="mini ?'pa-5 render-area width-change maximize' :'pa-5 render-area width-change'">
            <template v-if="selectedDataObjects.length > 0 || analysisFileShown">
                <shape-viewer
                    :data="renderData"
                    :metaData="renderMetaData"
                    :rows="rows"
                    :columns="cols"
                    :glyph-size="particleSize"
                    :currentTab="tab || ''"
                />
            </template>
            <span v-else>Select any number of data objects</span>
        </div>
    </div>
</template>

<style>
.context-card {
    display: flex;
    column-gap: 40px;
    padding: 10px 20px;
    width: 100%;
    height: 80px;
}
.content-area {
    position: relative;
    min-height: calc(100vh - 161px);
    background-color: #1e1e1e;
}
.width-change {
    position: absolute;
    left: 650px;
    width: calc(100% - 650px);
}
.maximize {
    left: 60px;
    width: calc(100% - 60px);
}
.render-area {
    display: flex;
    top: 75px;
    height: calc(100% - 70px);
}
.render-area > * {
    flex-grow: 1;
}
</style>
