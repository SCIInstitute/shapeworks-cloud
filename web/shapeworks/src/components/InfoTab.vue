<script>
import {
    landmarkInfo,
    selectedDataset,
    selectedProject,
    allSubjectsForDataset,
    anatomies,
    allSetLandmarks,
    landmarkSize,
    layersShown,
    selectedDataObjects,
    allDataObjectsInDataset,
    currentLandmarkPlacement,
    reassignLandmarkIDsByIndex,
    reassignLandmarkNumSetValues,
} from '@/store';
import { computed, onMounted, ref, watch } from 'vue';
import { saveLandmarkData } from '@/api/rest'

export default {
    setup() {
        const headers =  [
            {text: '', value: 'color', width: '20px', sortable: false},
            {text: 'Name', value: 'name', width: '120px'},
            {text: 'Comment', value: 'comment', width: '150px'},
            {text: 'Domain', value: 'domain', width: '100px'},
            {text: '# set', value: 'num_set', width: '60px', sortable: false},
        ];

        const changesMade = ref(false);

        const dialogs = ref([]);

        const expandedRows = ref([]);

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
                    const anatomyIndex = anatomies.value.findIndex((a) => a.replace('anatomy_', '') === l.domain)
                    const shapeKey = `${s.name}_${anatomyIndex}`
                    const landmarkKey = `${shapeKey}_${l.id}`
                    const numSet = allSetLandmarks.value[shapeKey]?.length || 0
                    const indexForDomain = landmarkInfo.value.filter(
                        (i) => i.domain === l.domain
                    ).map((i) => i.id).indexOf(l.id)
                    if (currentLandmarkPlacement.value === landmarkKey) {
                        placementStatus = `Click anywhere on ${s.name} ${l.domain}`
                    } else if (allSetLandmarks.value[shapeKey] && numSet > indexForDomain) {
                        const coordinateStrings = []
                        allSetLandmarks.value[shapeKey][indexForDomain].forEach((v) => {
                            coordinateStrings.push(v.toFixed(2))
                        })
                        placementStatus = coordinateStrings.join(', ')
                    } else if (indexForDomain >= numSet + 1) {
                        // Check if any previous landmarks are missing placements on this shape
                        const preReqLandmark = landmarkInfo.value[numSet]?.name
                        placementStatus = `${preReqLandmark} must be set first.`
                    }
                    statuses[l.id][shapeKey] = placementStatus
                })
            })
            return statuses
        })

        function getPlacementStatus(lInfo, subjectName) {
            const anatomyIndex = anatomies.value.findIndex((a) => a.replace('anatomy_', '') === lInfo.domain)
            const shapeKey = `${subjectName}_${anatomyIndex}`
            return placementStatuses.value[lInfo.id][shapeKey]
        }

        function beginPlacement(subject, item) {
            const anatomyIndex = anatomies.value.findIndex((a) => a.replace('anatomy_', '') === item.domain)
            currentLandmarkPlacement.value = `${subject.name}_${anatomyIndex}_${item.id}`
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
            changesMade.value = true
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

        function deleteLandmark(landmarkIndex, landmarkDomain) {
            const indexForDomain = landmarkInfo.value.filter(
                (i) => i.domain === landmarkDomain
            ).map((i) => i.id).indexOf(landmarkIndex)
            landmarkInfo.value.splice(landmarkIndex, 1)
            allSetLandmarks.value = Object.fromEntries(
                Object.entries(allSetLandmarks.value).map(
                    ([shapeKey, locations]) => {
                        if (locations.length > indexForDomain) {
                            locations.splice(indexForDomain, 1)
                        }
                        return [shapeKey, locations]
                    }
                ).filter(
                    ([, locations]) => locations.length
                )
            )
            reassignLandmarkIDsByIndex()
            dialogs.value = []
            expandedRows.value = []
            changesMade.value = true
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
                domain: anatomies.value[0].replace('anatomy_', ''),
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
            reassignLandmarkIDsByIndex()
            expandedRows.value = [landmark]
            selectedProject.value.landmarks = [
                ...selectedProject.value.landmarks,
                { newAddition: true }
            ]
            changesMade.value = true
        }

        function isShapeShown(subjectID, domain) {
            return selectedDataObjects.value.some((d) => (
                d.subject === subjectID && d.anatomy_type.replace('anatomy_', '') === domain
            ))
        }

        function showSubject(subjectID, domain) {
            const shape = allDataObjectsInDataset.value.find((d) => (
                d.subject === subjectID && d.anatomy_type.replace('anatomy_', '') === domain
            ))
            if (shape) {
                selectedDataObjects.value = [
                    ...selectedDataObjects.value,
                    shape
                ]
            }
        }

        function submit() {
            const locationData = {}
            Object.entries(allSetLandmarks.value).forEach(
                ([shapeKey, landmarkLocations]) => {
                    const anatomyIndex = shapeKey.split('_')[shapeKey.split('_').length - 1]
                    const anatomyType = anatomies.value[anatomyIndex]
                    const subjectName = shapeKey.replace('_'+anatomyIndex, '')
                    const subjectID = allSubjectsForDataset.value.find((s) => s.name === subjectName)?.id

                    if (!locationData[subjectID]) locationData[subjectID] = {}
                    locationData[subjectID][anatomyType] = landmarkLocations
                }
            )
            saveLandmarkData(
                selectedProject.value.id,
                landmarkInfo.value || {},
                locationData
            ).then((response) => {
                if (response.id === selectedProject.value.id) {
                    selectedProject.value = response
                    changesMade.value = false
                }
            })
        }

        watch(allSetLandmarks, () => changesMade.value = true)
        watch(currentLandmarkPlacement, (curr) => {
            reassignLandmarkNumSetValues()
            if (!curr) changesMade.value = true
        })

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
            changesMade,
            dialogs,
            anatomies,
            expandedRows,
            landmarkInfo,
            landmarkSize,
            currentLandmarkPlacement,
            colorStrings,
            placementStatuses,
            getPlacementStatus,
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
                                v-model="item.domain"
                                :items="anatomies.map((a) => a.replace('anatomy_', ''))"
                                style="width: 80px"
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
                                        <v-btn
                                            v-if="!currentLandmarkPlacement && getPlacementStatus(item, subject.name) === 'NOT SET' && isShapeShown(subject.id, item.domain)"
                                            @click="beginPlacement(subject, item)"
                                            small
                                        >
                                            BEGIN PLACEMENT
                                        </v-btn>
                                        <span v-else>
                                            {{ getPlacementStatus(item, subject.name) }}
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
                        <v-btn v-if="changesMade" color="primary" @click="submit">
                            Save Landmarks
                        </v-btn>
                        <span v-else>Landmarks Saved.</span>
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
