<script>
import {
    landmarkInfo,
    activeLandmark,
    selectedDataset,
    selectedProject,
    allSubjectsForDataset,
    landmarkWidgets,
    layersShown,
    selectedDataObjects
} from '@/store';
import { computed, onMounted, ref } from 'vue';
import { saveLandmarkData } from '@/api/rest'
import { landmarkSize } from '../store/index';

export default {
    setup() {
        const headers =  [
            {text: 'ID', value: 'id', width: '15px'},
            {text: '', value: 'color', width: '15px'},
            {text: 'Name', value: 'name', width: '100px'},
            {text: 'Comment', value: 'comment'},
            {text: '# set', value: 'num_set', width: '70px'},
        ];
        const colorDialog = ref(false);

        const colorStrings = computed(() => {
            return landmarkInfo.value.map(({color}) => {
                return `rgb(${color[0]},${color[1]},${color[2]})`
            })
        })

        function getColorObject(rgb) {
            return {
                'r': rgb[0],
                'g': rgb[1],
                'b': rgb[2]
            }
        }

        function updateLandmarkInfo(landmarkIndex, name, comment) {
            landmarkInfo.value[landmarkIndex] = Object.assign(
                {}, landmarkInfo.value[landmarkIndex], {name, comment}
            )
        }

        function updateLandmarkColor(landmarkIndex, color) {
            color = [
                color.rgba.r, color.rgba.g, color.rgba.b
            ]
            landmarkInfo.value[landmarkIndex] = Object.assign(
                {}, landmarkInfo.value[landmarkIndex], {color}
            )
            // overwrite landmarkInfo so colorStrings will recompute
            landmarkInfo.value = [...landmarkInfo.value]
        }

        function submit() {
            const landmarksLocations = {}
            allSubjectsForDataset.value.forEach((subject) => {
                const shapesShown = selectedDataObjects.value.filter((o) => o.subject === subject.id)
                shapesShown.forEach((shape, actorIndex) => {
                    landmarkInfo.value.forEach((lInfo) => {
                        const anatomyId = shape.anatomy_type
                        let widgetId = `${subject.name}_${actorIndex}_${lInfo.id}`
                        const widget = landmarkWidgets.value[widgetId]
                        if (widget) {
                            if (!landmarksLocations[subject.id]) {
                                landmarksLocations[subject.id] = {}
                            }
                            if (!landmarksLocations[subject.id][anatomyId]) {
                                landmarksLocations[subject.id][anatomyId] = []
                            }
                            const handle = widget.getWidgetState().getMoveHandle();
                            landmarksLocations[subject.id][anatomyId].push(handle.getOrigin())
                        }

                    })
                })
            })
            saveLandmarkData(
                selectedProject.value.id,
                landmarkInfo.value,
                landmarksLocations
            ).then((response) => {
                console.log(response)
            })
        }

        onMounted(() => {
            if (!layersShown.value.includes('Landmarks')) {
                layersShown.value = [...layersShown.value, 'Landmarks']
            }
        })

        return {
            selectedDataset,
            selectedProject,
            allSubjectsForDataset,
            headers,
            landmarkInfo,
            landmarkSize,
            activeLandmark,
            colorStrings,
            colorDialog,
            getColorObject,
            updateLandmarkInfo,
            updateLandmarkColor,
            submit,
        }
    }
}
</script>

<template>
    <div class="pa-3">
        <div class="pa-3">
            View other project information
        </div>
        <v-expansion-panels :value="0">
            <v-expansion-panel>
                <v-expansion-panel-header>
                    Landmarks
                    <v-spacer/>
                    <v-text-field
                        v-model.number="landmarkSize"
                        label="Size"
                        type="number"
                        min="1"
                        max="15"
                        style="max-width: 50px"
                        @click.stop
                    />
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-data-table
                        :value="[activeLandmark]"
                        :headers="headers"
                        :items="landmarkInfo"
                        item-key="id"
                        disable-pagination
                        hide-default-footer
                        single-select
                        dense
                        width="100%"
                        @click:row="(l) => activeLandmark = l"
                    >
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.color="{ index, item }">
                            <v-dialog width="300">
                            <template v-slot:activator="{ on, attrs }">
                                <v-btn
                                    class='color-square'
                                    :style="{backgroundColor: colorStrings[index]}"
                                    v-bind="attrs"
                                    v-on="on"
                                />
                            </template>
                            <v-card>
                                <v-card-title>Change color for {{ item.name }}</v-card-title>
                                <v-color-picker
                                    :value="getColorObject(item.color)"
                                    dot-size="25"
                                    @update:color="(c) => updateLandmarkColor(index, c)"
                                ></v-color-picker>
                            </v-card>
                            </v-dialog>
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.name="{ index, item }">
                            <v-text-field
                                v-model="item.name"
                                @input="(v) => updateLandmarkInfo(index, v, item.comment)"
                            />
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.comment="{ index, item }">
                            <v-text-field
                                v-model="item.comment"
                                @input="(v) => updateLandmarkInfo(index, item.name, v)"
                            />
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.num_set="{ item }">
                            {{ item.num_set }} / {{ allSubjectsForDataset.length }}
                        </template>
                    </v-data-table>
                    <v-btn
                        style="width: 100%"
                        color="primary"
                        @click="submit"
                    >
                        Save Landmarks
                    </v-btn>
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
    </div>
</template>

<style>
.file-column {
    width: 100px!important;
    overflow: hidden;
    text-overflow: ellipsis;
}
.v-data-table td {
    border-bottom: none !important;
}
.v-row-group__header {
    background: none !important;
    border-top: 1px solid white !important;
}
.color-square {
    height: 20px !important;
    width: 20px !important;
    min-width: 15px !important;
    padding: 0 !important;
}
</style>
