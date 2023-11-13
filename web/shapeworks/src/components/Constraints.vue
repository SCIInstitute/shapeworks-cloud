<script>
import { onMounted, ref } from 'vue';
import {
    constraintInfo,
    selectedProject,
    allSubjectsForDataset,
    anatomies,
    allSetConstraints,
    currentConstraintPlacement,
    reassignConstraintIDsByIndex,
    layersShown,
    layers,
} from '@/store';
import { getShapeKey, isShapeShown, showShape, getDomainIndex } from '../store/methods';

export default {
    setup() {
        const headers =  [
            {text: '', value: 'id', width: '20px', sortable: false},
            {text: 'Type', value: 'type', width: '270px', sortable: false},
            {text: 'Domain', value: 'domain', width: '100px'},
            {text: '# set', value: 'num_set', width: '60px', sortable: false},
        ];

        const changesMade = ref(false);

        const expandedRows = ref([]);

        const dialogs = ref([]);

        function getSameDomainConstraints(item) {
            return constraintInfo.value.filter(
                (i) => i.domain === item.domain
            )
        }

        function getShapePlacementIndex(item) {
            return  getSameDomainConstraints(item).map((i) => i.id).indexOf(item.id)
        }

        function getPlacementStatus(item, subject) {
            const shapeKey = getShapeKey(item, subject)
            const currentShapePlacements = allSetConstraints.value[shapeKey]
            const shapePlacementIndex = getShapePlacementIndex(item)
            if (currentShapePlacements && currentShapePlacements.length > shapePlacementIndex) {
                const placement = currentShapePlacements[shapePlacementIndex]
                return placement.type + ' placed'
            }
            else if (currentConstraintPlacement.value === shapeKey) {
                if (item.type === 'plane') return `Configure plane placement on ${subject.name} ${item.domain}`
                if (item.type === 'paint') return `Draw anywhere on ${subject.name} ${item.domain}`
            }
            return 'NOT SET'
        }

        function beginPlacement(subject, item) {
            currentConstraintPlacement.value = `${getShapeKey(item, subject)}_${item.id}`
        }


        function newConstraint() {
            const newID = constraintInfo.value?.length || 0
            const constraint = {
                type: 'plane',
                domain: anatomies.value[0].replace('anatomy_', ''),
                id: newID,
                num_set: 0,
                visible: true,
            }
            if (constraintInfo.value?.length) {
                constraintInfo.value = [
                    ...constraintInfo.value,
                    constraint
                ]
            } else {
                constraintInfo.value = [constraint]
            }
            reassignConstraintIDsByIndex()
            expandedRows.value = [constraint]
            selectedProject.value.constraints = [
                ...selectedProject.value.constraints,
                { newAddition: true }
            ]
            changesMade.value = true
        }

        function deleteConstraint(item) {
            const domainIndex =  getDomainIndex(item)
            const shapePlacementIndex = getShapePlacementIndex(item)
            allSetConstraints.value = Object.fromEntries(
                Object.entries(allSetConstraints.value).map(
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
            constraintInfo.value.splice(item.id, 1)
            reassignConstraintIDsByIndex()
            currentConstraintPlacement.value = undefined
            dialogs.value = []
            expandedRows.value = []
            changesMade.value = true
        }

        function submit() {
            const locationData = {}
            Object.entries(allSetConstraints.value).forEach(
                ([shapeKey, constraintLocations]) => {
                    const splitShapeKey = shapeKey.split('_')
                    const anatomyIndex = shapeKey.split('_')[shapeKey.split('_').length - 1]
                    const anatomyType = anatomies.value[anatomyIndex]
                    const subjectName = splitShapeKey.slice(0, splitShapeKey.length - 1).join('_')
                    const subjectID = allSubjectsForDataset.value.find((s) => s.name === subjectName)?.id

                    if(subjectID) {
                        if (!locationData[subjectID]) locationData[subjectID] = {}
                        locationData[subjectID][anatomyType] = constraintLocations
                    }
                }
            )
            console.log('submit constraints', constraintInfo.value, locationData)
            // saveConstraintData(
            //     selectedProject.value.id,
            //     constraintInfo.value || {},
            //     locationData
            // ).then((response) => {
            //     if (response.id === selectedProject.value.id) {
            //         selectedProject.value = response
            //         changesMade.value = false
            //     }
            // })
        }

        onMounted(() => {
            if (
                !layersShown.value.includes('Constraints') &&
                layers.value.find(l => l.name === 'Constraints')?.available()
            ) {
                layersShown.value = [...layersShown.value, 'Constraints']
            }
        })

        return {
            headers,
            changesMade,
            dialogs,
            expandedRows,
            constraintInfo,
            anatomies,
            allSubjectsForDataset,
            currentConstraintPlacement,
            isShapeShown,
            showShape,
            getPlacementStatus,
            beginPlacement,
            newConstraint,
            deleteConstraint,
            submit,
        }
    }
}
</script>

<template>
    <v-expansion-panel>
                <v-expansion-panel-header>
                    Constraints
                    <v-spacer/>
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-data-table
                        :headers="headers"
                        :items="constraintInfo"
                        :expanded="expandedRows"
                        item-key="id"
                        disable-pagination
                        hide-default-footer
                        single-select
                        dense
                        width="100%"
                    >
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.id="{ index, item }">
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
                                        <v-btn color="red" @click="deleteConstraint(item)">
                                            Yes, Delete This Constraint
                                        </v-btn>
                                    </v-card-actions>
                                </v-card>
                            </v-dialog>
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.type="{ index, item }">
                            <v-select
                                v-model="item.type"
                                :items="['plane', 'paint']"
                                :disabled="item.num_set > 0"
                                style="width: 270px"
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
                                            v-if="!currentConstraintPlacement && getPlacementStatus(item, subject) === 'NOT SET' && isShapeShown(subject.id, item.domain)"
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
                        <v-btn @click="newConstraint">
                            + New Constraint
                        </v-btn>
                        <v-btn v-if="changesMade" color="primary" @click="submit">
                            Save Constraints
                        </v-btn>
                        <span v-else>Constraints Saved.</span>
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
    bottom: 30%
}
</style>
