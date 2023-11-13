<script>
import { computed, onMounted, ref, watch } from 'vue';
import {
    landmarkInfo,
    selectedProject,
    allSubjectsForDataset,
    anatomies,
    allSetLandmarks,
    landmarkSize,
    layersShown,
    currentLandmarkPlacement,
    reassignLandmarkIDsByIndex,
    reassignLandmarkNumSetValues,
} from '@/store';
import { saveLandmarkData } from '@/api/rest'
import { getShapeKey, isShapeShown, showShape, getDomainIndex } from '../store/methods';

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

        const expandedRows = ref([]);

        const dialogs = ref([]);

        const colorStrings = computed(() => {
            return landmarkInfo.value.map(({color}) => {
                return `rgb(${color[0]},${color[1]},${color[2]})`
            })
        })

        function getColorObject(rgb) {
            return {'r': rgb[0], 'g': rgb[1], 'b': rgb[2]}
        }

        function getSameDomainLandmarks(item) {
            return landmarkInfo.value.filter(
                (i) => i.domain === item.domain
            )
        }

        function getShapePlacementIndex(item) {
            return  getSameDomainLandmarks(item).map((i) => i.id).indexOf(item.id)
        }

        function getPlacementStatus(item, subject) {
            const shapeKey = getShapeKey(item, subject)
            const currentShapePlacements = allSetLandmarks.value[shapeKey]
            const shapePlacementIndex = getShapePlacementIndex(item)
            if (currentShapePlacements && currentShapePlacements.length > shapePlacementIndex) {
                const placement = currentShapePlacements[shapePlacementIndex]
                const coordStrings = []
                placement.forEach(v => coordStrings.push(v.toFixed(2)))
                return coordStrings.join(", ")
            }
            else if (shapePlacementIndex >= (currentShapePlacements?.length || 0) + 1) {
                const preReq = getSameDomainLandmarks(item)[currentShapePlacements?.length || 0]
                return `${preReq.name} must be set first.`
            }
            else if (currentLandmarkPlacement.value === shapeKey) {
                return `Click anywhere on ${subject.name} ${item.domain}`
            }
            return 'NOT SET'
        }

        function beginPlacement(subject, item) {
            currentLandmarkPlacement.value = `${getShapeKey(item, subject)}_${item.id}`
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

        function deleteLandmark(item) {
            const domainIndex =  getDomainIndex(item)
            const shapePlacementIndex = getShapePlacementIndex(item)
            allSetLandmarks.value = Object.fromEntries(
                Object.entries(allSetLandmarks.value).map(
                    ([shapeKey, locations]) => {
                        if (shapeKey.split('_').includes(domainIndex.toString()) && locations.length > shapePlacementIndex) {
                            locations.splice(shapePlacementIndex, 1)
                        }
                        return [shapeKey, locations]
                    }
                ).filter(
                    ([, locations]) => locations.length
                )
            )
            landmarkInfo.value.splice(item.id, 1)
            reassignLandmarkIDsByIndex()
            currentLandmarkPlacement.value = undefined
            dialogs.value = []
            expandedRows.value = []
            changesMade.value = true
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


        function submit() {
            const locationData = {}
            Object.entries(allSetLandmarks.value).forEach(
                ([shapeKey, landmarkLocations]) => {
                    const splitShapeKey = shapeKey.split('_')
                    const anatomyIndex = shapeKey.split('_')[shapeKey.split('_').length - 1]
                    const anatomyType = anatomies.value[anatomyIndex]
                    const subjectName = splitShapeKey.slice(0, splitShapeKey.length - 1).join('_')
                    const subjectID = allSubjectsForDataset.value.find((s) => s.name === subjectName)?.id

                    if(subjectID) {
                        if (!locationData[subjectID]) locationData[subjectID] = {}
                        locationData[subjectID][anatomyType] = landmarkLocations
                    }
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
            headers,
            changesMade,
            dialogs,
            expandedRows,
            colorStrings,
            landmarkSize,
            landmarkInfo,
            anatomies,
            allSubjectsForDataset,
            currentLandmarkPlacement,
            isShapeShown,
            showShape,
            getColorObject,
            getPlacementStatus,
            beginPlacement,
            newLandmark,
            deleteLandmark,
            updateLandmarkColor,
            updateLandmarkInfo,
            submit,
        }
    }
}
</script>

<template>
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
                                        <v-btn color="red" @click="deleteLandmark(item)">
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
                                :disabled="item.num_set > 0"
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
                                        @click="showShape(subject.id, item.domain)"
                                    >
                                        Show subject
                                    </v-btn>
                                    <v-spacer v-else />
                                    <div
                                        v-if="getPlacementStatus(item, subject)"
                                        style="width: 170px; text-align: right;"
                                    >
                                        <v-btn
                                            v-if="!currentLandmarkPlacement && getPlacementStatus(item, subject) === 'NOT SET' && isShapeShown(subject.id, item.domain)"
                                            @click="beginPlacement(subject, item)"
                                            small
                                        >
                                            BEGIN PLACEMENT
                                        </v-btn>
                                        <span v-else>
                                            {{ getPlacementStatus(item, subject) }}
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
