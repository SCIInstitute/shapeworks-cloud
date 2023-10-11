<script>
import {
    landmarkInfo,
    activeLandmark,
    selectedDataset,
    selectedProject,
    allSubjectsForDataset,
    landmarkWidgets,
    layersShown,
    selectedDataObjects,
    allDataObjectsInDataset,
} from '@/store';
import { computed, onMounted, ref } from 'vue';
import { saveLandmarkData } from '@/api/rest'
import { landmarkSize } from '../store/index';

export default {
    setup() {
        const headers =  [
            {text: '', value: 'color', width: '20px', sortable: false},
            {text: 'Name', value: 'name', width: '120px'},
            {text: 'Comment', value: 'comment', width: '160px'},
            {text: 'Domain', value: 'domain', width: '100px'},
            {text: '# set', value: 'num_set', width: '60px', sortable: false},
        ];

        const dialogs = ref([]);

        const expandedRows = ref([]);

        const anatomies = computed(() => {
            return allDataObjectsInDataset.value.map((obj) => obj.anatomy_type)
        })

        const colorStrings = computed(() => {
            return landmarkInfo.value.map(({color}) => {
                return `rgb(${color[0]},${color[1]},${color[2]})`
            })
        })

        function fetchAllLandmarkCoords() {
            if (selectedProject.value) {
                selectedProject.value.landmarks.forEach((l) => {
                    console.log(l.subject, l.anatomy_type, l.file)
                })
            }
        }

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

        function reassignIDsByIndex() {
            landmarkInfo.value = landmarkInfo.value.map((info, index) => {
                return Object.assign(info, {id: index})
            })
        }

        function deleteLandmark(landmarkIndex) {
            landmarkInfo.value.splice(landmarkIndex, 1)
            reassignIDsByIndex()
            dialogs.value = []
            expandedRows.value = []
        }

        function newLandmark() {
            const landmark = {
                color: [0, 100, 255],
                comment: 'New Comment',
                domain: anatomies.value[0],
                id: landmarkInfo.value.length,
                name: 'New Landmark',
                num_set: 0,
                visible: true,
            }
            landmarkInfo.value = [
                ...landmarkInfo.value,
                landmark
            ]
            reassignIDsByIndex()
            expandedRows.value = [landmark]
        }

        function isLandmarkSetForShape(landmarkIndex, subjectID, domain) {
            console.log(landmarkIndex, subjectID, domain)
        }

        function isShapeShown(subjectID, domain) {
            return selectedDataObjects.value.some((d) => (
                d.subject === subjectID && anatomies.value.indexOf(d.anatomy_type) === parseInt(domain)
            ))
        }

        function showShape(subjectID, domain) {
            const shape = allDataObjectsInDataset.value.find((d) => (
                d.subject === subjectID && anatomies.value.indexOf(d.anatomy_type) === parseInt(domain)
            ))
            if (shape) {
                selectedDataObjects.value = [
                    ...selectedDataObjects.value,
                    shape
                ]
            }
            console.log('show', shape)
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
            fetchAllLandmarkCoords()
            if (!layersShown.value.includes('Landmarks')) {
                layersShown.value = [...layersShown.value, 'Landmarks']
            }
        })

        return {
            selectedDataset,
            selectedProject,
            allSubjectsForDataset,
            headers,
            dialogs,
            anatomies,
            expandedRows,
            landmarkInfo,
            landmarkSize,
            activeLandmark,
            colorStrings,
            getColorObject,
            updateLandmarkInfo,
            updateLandmarkColor,
            deleteLandmark,
            newLandmark,
            isLandmarkSetForShape,
            isShapeShown,
            showShape,
            submit,
        }
    }
}
</script>

<template>
    <div>
        <div class="pa-6">
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
                        :expanded="expandedRows"
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
                            <v-dialog
                                v-model="dialogs[index]"
                                value="index"
                                width="400"
                            >
                                <template v-slot:activator="{ on, attrs }">
                                    <v-icon class="delete-icon" v-bind="attrs" v-on="on">
                                        mdi-trash-can
                                    </v-icon>
                                </template>
                                <v-card>
                                    <v-card-title style="word-break: break-word;">
                                        Are you sure you want to remove {{ item.name }}
                                        on all subjects?
                                    </v-card-title>
                                    <v-card-actions>
                                        <v-spacer/>
                                        <v-btn color="warning" @click="deleteLandmark(index)">
                                            Yes, Delete This Landmark
                                        </v-btn>
                                    </v-card-actions>
                                </v-card>
                            </v-dialog>
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
                                style="width: 100px"
                                @input="(v) => updateLandmarkInfo(index, v, item.comment)"
                            />
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.comment="{ index, item }">
                            <v-text-field
                                v-model="item.comment"
                                style="width: 100px"
                                @input="(v) => updateLandmarkInfo(index, item.name, v)"
                            />
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.domain="{ index, item }">
                            <v-select
                                :value="anatomies[item.domain]"
                                :items="anatomies"
                                style="width: 100px"
                                @update="(v) => item.domain = anatomies.indexOf(v)"
                            />
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.num_set="{ item }">
                            <div style="width: 60px; text-align: right;">
                                {{ item.num_set }} / {{ allSubjectsForDataset.length }}
                                <v-icon v-if="expandedRows.includes(item)" @click="expandedRows=[]">mdi-menu-up</v-icon>
                                <v-icon v-else @click="expandedRows=[item]">mdi-menu-down</v-icon>
                            </div>
                        </template>
                        <template v-slot:expanded-item="{ item }">
                            <div style="width: 100%">
                                Click anywhere on each subject to place {{ item.name }}.
                                <div
                                    v-for="subject in allSubjectsForDataset"
                                    :key="subject.id"
                                    class="d-flex py-1"
                                    style="align-items: center; justify-content: space-between; width: 100%"
                                >
                                    <span>{{ subject.name }}</span>
                                    <v-btn
                                        small
                                        v-if="!isShapeShown(subject.id, item.domain)"
                                        @click="showShape(subject.id, item.domain)"
                                    >
                                        Show shape
                                    </v-btn>
                                    <v-spacer v-else />
                                    <span>{{ !isLandmarkSetForShape(item.id, subject.id, item.domain) && 'NOT '}}SET</span>
                                </div>
                            </div>
                        </template>
                    </v-data-table>
                    <div class="d-flex py-3" style="justify-content: space-between;">
                        <v-btn @click="newLandmark">
                            + New Landmark
                        </v-btn>
                        <v-btn color="primary" @click="submit">
                            Save Landmarks
                        </v-btn>
                    </div>
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
.v-data-table tr {
    position: relative;
    display: block;
    padding-left: 25px;
}
.v-data-table td {
    border-bottom: none !important;
    padding: 0px 10px !important;
}
.v-data-table__expanded {
    width: 100%
}
.v-row-group__header {
    background: none !important;
    border-top: 1px solid white !important;
}
.delete-icon {
    position: absolute !important;
    left: 5px;
}
.color-square {
    height: 20px !important;
    width: 20px !important;
    min-width: 15px !important;
    padding: 0 !important;
}
</style>
