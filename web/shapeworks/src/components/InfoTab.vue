<script>
import { landmarkInfo, activeLandmark, selectedDataset, selectedProject, allSubjectsForDataset } from '@/store';
import { computed, ref } from 'vue';

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
        const changesMade = ref(false);

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
            changesMade.value = true;
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
            changesMade.value = true;
        }

        return {
            selectedDataset,
            selectedProject,
            allSubjectsForDataset,
            headers,
            landmarkInfo,
            activeLandmark,
            colorStrings,
            getColorObject,
            updateLandmarkInfo,
            updateLandmarkColor,
            colorDialog,
            changesMade,
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
                    <v-btn v-if="changesMade" style="width: 100%" color="primary">Save Changes</v-btn>
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
