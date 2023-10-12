<script>
import {
    landmarkInfo,
    selectedDataset,
    selectedProject,
    allSubjectsForDataset,
    landmarkWidgets,
    allSetLandmarks,
    layersShown,
    selectedDataObjects,
    allDataObjectsInDataset,
    currentLandmarkPlacement,
} from '@/store';
import { computed, onMounted, ref, watch } from 'vue';
import { saveLandmarkData } from '@/api/rest'
import { landmarkSize } from '../store/index';
import pointsReader from '@/reader/points';

export default {
    setup() {
        const headers =  [
            {text: '', value: 'color', width: '20px', sortable: false},
            {text: 'Name', value: 'name', width: '120px'},
            {text: 'Comment', value: 'comment', width: '150px'},
            {text: 'Domain', value: 'domain', width: '100px'},
            {text: '# set', value: 'num_set', width: '60px', sortable: false},
        ];

        const dialogs = ref([]);

        const expandedRows = ref([]);

        const anatomies = computed(() => {
            return allDataObjectsInDataset.value.map((obj) => obj.anatomy_type.replace('anatomy_', ''))
        })

        const colorStrings = computed(() => {
            return landmarkInfo.value.map(({color}) => {
                return `rgb(${color[0]},${color[1]},${color[2]})`
            })
        })

        const placementStatuses = computed(() => {
            const statuses = {}
            landmarkInfo.value.forEach((l) => {
                statuses[l.id] = {}
                allSubjectsForDataset.value.forEach((s) => {
                    let placementStatus = 'NOT SET';
                    const anatomyIndex = anatomies.value.indexOf(l.domain)
                    const shapeKey = `${s.name}_${anatomyIndex}`
                    if (allSetLandmarks.value[shapeKey]) {
                        if (allSetLandmarks.value[shapeKey].length > l.id) {
                            if (!allSetLandmarks.value[shapeKey][l.id]) {
                                console.log(allSetLandmarks.value[shapeKey])
                            }
                            placementStatus = allSetLandmarks.value[shapeKey][l.id].map(
                                (v) => v.toFixed(2)
                            ).join(', ')
                        } else if (allSetLandmarks.value[shapeKey].length < l.id) {
                            // Check if any previous landmarks are missing placements on this shape
                            const preReqLandmark = landmarkInfo.value[allSetLandmarks.value[shapeKey].length]?.name
                            placementStatus = `${preReqLandmark} must be set first.`
                        }
                    }
                    statuses[l.id][s.name] = placementStatus
                })
            })
            return statuses
        })

        function fetchAllLandmarkCoords() {
            if (selectedProject.value) {
                selectedProject.value.landmarks.forEach((l) => {
                    const subjectName = allSubjectsForDataset.value.find((s) => s.id == l.subject)?.name
                    const anatomyIndex = anatomies.value.indexOf(l.anatomy_type.replace('anatomy_', ''))
                    const shapeKey = `${subjectName}_${anatomyIndex}`
                    pointsReader(l.file).then((points) => {
                        const landmarkPointData = Array.from(points.getPoints().getData())
                        const landmarkArray = []
                        while (landmarkPointData.length) {
                            landmarkArray.push(landmarkPointData.splice(0, 3))
                        }
                        allSetLandmarks.value[shapeKey] = landmarkArray
                    })
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
            // reassign store var for listeners
            landmarkInfo.value = [...landmarkInfo.value]
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

        function reassignNumSetValues() {
            landmarkInfo.value = landmarkInfo.value.map((l) => {
                const subjectName = allSubjectsForDataset.value.find((s) => s.id == l.subject)?.name
                const anatomyIndex = anatomies.value.indexOf(l.domain)
                const shapeKey = `${subjectName}_${anatomyIndex}`
                return Object.assign(l, {
                    num_set: allSetLandmarks.value[shapeKey]?.length || 0
                })
            })
        }

        function deleteLandmark(landmarkIndex) {
            landmarkInfo.value.splice(landmarkIndex, 1)
            reassignIDsByIndex()
            dialogs.value = []
            expandedRows.value = []
        }

        function newLandmark() {
            const newID = landmarkInfo.value?.length || 0
            const landmark = {
                color: [
                    100 * (newID % 2),
                    50 * (newID % 5),
                    80 * (newID % 3)
                ],
                comment: '',
                domain: anatomies.value[0],
                id: newID,
                name: `L${newID}`,
                num_set: 0,
                visible: true,
            }
            if (landmarkInfo.value?.length) {
                landmarkInfo.value = [
                    ...landmarkInfo.value,
                    landmark
                ]
            } else {
                landmarkInfo.value = [landmark]
            }
            reassignIDsByIndex()
            expandedRows.value = [landmark]
        }

        function isShapeShown(subjectID, domain) {
            return selectedDataObjects.value.some((d) => (
                d.subject === subjectID && d.anatomy_type.replace('anatomy_', '') === domain
            ))
        }

        function showSubject(subjectID, domain) {
            selectedDataObjects.value = allDataObjectsInDataset.value.filter((d) => {
                (
                    d.subject == subjectID &&
                    d.anatomy_type.replace('anatomy_', '') === domain
                ) || selectedDataObjects.value.includes(d)
            })
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

        watch(allSetLandmarks, reassignNumSetValues)

        onMounted(() => {
            fetchAllLandmarkCoords()
            if (!layersShown.value.includes('Landmarks')) {
                layersShown.value = [...layersShown.value, 'Landmarks']
            }
        })

        function beginPlacement(subject, item){
            currentLandmarkPlacement.value = `${subject.name}_${anatomies.value.indexOf(item.domain)}_${item.id}`
        }

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
            currentLandmarkPlacement,
            colorStrings,
            placementStatuses,
            getColorObject,
            updateLandmarkInfo,
            updateLandmarkColor,
            deleteLandmark,
            newLandmark,
            isShapeShown,
            showSubject,
            submit,
            beginPlacement
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
                        :headers="headers"
                        :items="landmarkInfo"
                        :expanded="expandedRows"
                        item-key="id"
                        disable-pagination
                        hide-default-footer
                        single-select
                        dense
                        width="100%"
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
                                style="width: 130px"
                                @input="(v) => updateLandmarkInfo(index, item.name, v)"
                            />
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.domain="{ index, item }">
                            <v-select
                                :value="anatomies[item.domain]"
                                :items="anatomies"
                                style="width: 80px"
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
                                <div
                                    v-for="subject in allSubjectsForDataset"
                                    :key="subject.id"
                                    class="d-flex py-1"
                                    style="align-items: center; justify-content: space-between; width: 100%"
                                >
                                    <span style="width: 170px;">{{ subject.name }}</span>
                                    <v-btn
                                        small
                                        v-if="!isShapeShown(subject.id, item.domain)"
                                        @click="showSubject(subject.id, item.domain)"
                                    >
                                        Show subject
                                    </v-btn>
                                    <v-spacer v-else />
                                    <div
                                        v-if="placementStatuses[item.id]"
                                        style="width: 170px; text-align: right;"
                                    >
                                        <span v-if="currentLandmarkPlacement === `${subject.name}_${anatomies.indexOf(item.domain)}_${item.id}`">
                                            Click anywhere on the target shape.
                                        </span>
                                        <v-btn
                                            v-else-if="!currentLandmarkPlacement && placementStatuses[item.id][subject.name] === 'NOT SET' && isShapeShown(subject.id, item.domain)"
                                            @click="beginPlacement(subject, item)"
                                            small
                                        >
                                            BEGIN PLACEMENT
                                        </v-btn>
                                        <span v-else>
                                            {{ placementStatuses[item.id][subject.name] }}
                                        </span>
                                    </div>
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
