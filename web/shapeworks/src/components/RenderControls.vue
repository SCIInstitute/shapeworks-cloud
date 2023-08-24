<script lang="ts">
import { setDatasetThumbnail, setProjectThumbnail } from '@/api/rest';
import { computed, ref, watch } from 'vue';
import {
    particleSize,
    layers,
    layersShown,
    orientationIndicator,
    selectedDataObjects,
    selectedDataset,
    selectedProject,
    vtkInstance,
    allDatasets,
    allProjectsForDataset,
    showDifferenceFromMeanMode,
    analysisFileShown,
    showGoodBadParticlesMode,
goodBadMaxAngle
} from '@/store';


export default {
    props: {
        currentTab: {
            type: String,
            required: true,
        }
    },
    setup(props, context) {
        orientationIndicator.value.setDefaultStyle({
            fontStyle: 'bold',
            fontFamily: 'Arial',
            fontColor: 'black',
            faceColor: '#ffffff',
            faceRotation: 0,
            edgeThickness: 0.1,
            edgeColor: 'black',
            resolution: 400,
        })

        const axisSystemOptions = [
            {
                text: 'XYZ',
                value: 'xyz',
                xPlus: '+X',
                xMinus: '-X',
                yPlus: '+Y',
                yMinus: '-Y',
                zPlus: '+Z',
                zMinus: '-Z',
            },
            {
                text: 'Medical',
                value: 'slp',
                xPlus: 'L',
                xMinus: 'R',
                yPlus: 'P',
                yMinus: 'A',
                zPlus: 'S',
                zMinus: 'I',
            }
        ]
        const axisSystem = ref(axisSystemOptions.find(
            (system) => system.value === 'xyz'
        ))

        function changeAxisSystem(newSystemValue: string){
            const newSystem = axisSystemOptions.find(
                (system) => system.value == newSystemValue
            )
            if(newSystem){
                orientationIndicator.value.setXPlusFaceProperty({
                    text: newSystem.xPlus
                })
                orientationIndicator.value.setXMinusFaceProperty({
                    text: newSystem.xMinus
                })
                orientationIndicator.value.setYPlusFaceProperty({
                    text: newSystem.yPlus
                })
                orientationIndicator.value.setYMinusFaceProperty({
                    text: newSystem.yMinus
                })
                orientationIndicator.value.setZPlusFaceProperty({
                    text: newSystem.zPlus
                })
                orientationIndicator.value.setZMinusFaceProperty({
                    text: newSystem.zMinus
                })
                context.emit("change")
            }
        }
        changeAxisSystem('xyz')

        function resetView() {
            context.emit("change")
        }
        watch(showDifferenceFromMeanMode, resetView)
        watch(showGoodBadParticlesMode, resetView)
        watch(goodBadMaxAngle, resetView)

        const thumbnailTarget = computed(() => {
            if(layersShown.value.length === 1 && layersShown.value[0] === "Original") {
                // showing only original data object, valid for dataset thumbnail
                return {
                    type: 'Dataset',
                    id: selectedDataset.value?.id
                }
            } else {
                // valid for project thumbnail
                return {
                    type: 'Project',
                    id: selectedProject.value?.id
                }
            }
        })

        async function captureThumbnail() {
            if(vtkInstance.value) {
                vtkInstance.value.orientationCube.setEnabled(false)
                const encoded = (await Promise.all(
                    // method signature for captureImages is defined as returning void,
                    // but it returns a list of promises.
                    // @ts-ignore
                    vtkInstance.value.renderWindow.captureImages(
                        "image/png",
                        {
                            size: [100, 100]
                        }
                    )
                ))[0] as String
                const thumbnail = encoded.split(',')[1]
                if (thumbnailTarget.value.type === 'Dataset') {
                    if (thumbnailTarget.value.id) {
                        let dataset = await setDatasetThumbnail(thumbnailTarget.value.id, thumbnail)
                        if(dataset) {
                            allDatasets.value = allDatasets.value.map((d) => {
                                if (d.id === dataset.id) return dataset
                                return d
                            })
                            selectedDataset.value = dataset;
                        }
                    }
                } else {
                    if (thumbnailTarget.value.id) {
                        let project = await setProjectThumbnail(thumbnailTarget.value.id, thumbnail)
                        if(project) {
                            allProjectsForDataset.value = allProjectsForDataset.value.map((p) => {
                                if (p.id === project.id) return project
                                return p
                            })
                            selectedProject.value = project;
                        }
                    }
                }
                vtkInstance.value.orientationCube.setEnabled(true)
            }
        }

        const showAnalysisOptions = computed(() => {
            return props.currentTab === 'analyze' && analysisFileShown.value;
        })

        return {
            particleSize,
            layersShown,
            layers,
            axisSystem,
            axisSystemOptions,
            changeAxisSystem,
            resetView,
            selectedDataObjects,
            captureThumbnail,
            thumbnailTarget,
            showDifferenceFromMeanMode,
            showAnalysisOptions,
        }
    }
}
</script>

<template>
    <div class="render-control-bar">
        <v-select
            v-model="layersShown"
            v-if="!showAnalysisOptions"
            :items="layers"
            :item-disabled="(layer) => !layer.available()"
            item-value="name"
            label="Layers shown"
            style="width: 500px"
            multiple
            small-chips
            item-text="name"
        >
            <template #selection="{ item, index }">
                <v-chip
                    close
                    @click:close="layersShown.splice(index, 1)"
                    :color="item.color"
                    :text-color="item.color === 'white' ? 'black' : 'white'"
                >
                    {{ item.name }}
                </v-chip>
            </template>
        </v-select>
        <v-text-field
            v-model.number="particleSize"
            v-if="!showAnalysisOptions && layersShown.includes('Particles')"
            label="Particle Size"
            type="number"
            style="width: 80px"
            step="0.5"
            min="0.5"
            max="10"
            hide-details
        />
        <v-select
            v-bind="axisSystem"
            :items="axisSystemOptions"
            @change="changeAxisSystem"
            label="Axis System"
            style="width: 150px"
        />
        <v-switch
            v-if="showAnalysisOptions"
            v-model="showDifferenceFromMeanMode"
            label="Show difference from mean"
        />
        <v-btn
            class="my-5"
            v-if="!showAnalysisOptions && selectedDataObjects.length === 1"
            @click="captureThumbnail"
        >
            Set {{ thumbnailTarget.type }} thumbnail
        </v-btn>
        <v-btn
            class="my-5"
            @click="resetView"
        >
            Reset view
        </v-btn>
    </div>
</template>

<style scoped>
.render-control-bar {
    display: flex;
    width: 100%;
    height: 70px;
    justify-content: space-between;
    align-items: baseline;
    column-gap: 20px;
}
.render-control-bar > * {
    flex-grow: 0;
}
</style>
