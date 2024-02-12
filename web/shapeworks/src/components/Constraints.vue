<script>
import { ref, watch } from 'vue';
import {
    constraintInfo,
    constraintsShown,
    constraintPaintRadius,
    selectedProject,
    allSubjectsForDataset,
    anatomies,
    allSetConstraints,
    currentConstraintPlacement,
    reassignConstraintIDsByIndex,
} from '@/store';
import { getConstraintLocation, getWidgetInfo, isShapeShown, setConstraintLocation, toggleSubjectShown } from '../store/methods';
import { saveConstraintData } from '@/api/rest';
import { convertConstraintDataForDB } from '@/reader/constraints';
import { constraintPaintExclusion } from '../store/index';

export default {
    setup() {
        const headers =  [
            {text: '', value: 'id', width: '10px', sortable: false},
            {text: 'Show', value: 'show', width: '10px', sortable: false},
            {text: 'Type', value: 'type', width: '270px', sortable: false},
            {text: 'Domain', value: 'domain', width: '100px'},
            {text: '# set', value: 'num_set', width: '60px', sortable: false, align: 'end'},
        ];

        const changesMade = ref(false);

        const expandedRows = ref([]);

        const dialogs = ref([]);

        const constraintErrors = ref({});


        function getPlacementStatus(subject, item) {
            const placement = getConstraintLocation(subject, item)
            if (JSON.stringify(currentConstraintPlacement.value) === JSON.stringify(getWidgetInfo(subject, item))) {
                return 'PLACING'
            } else if (placement) {
                return item.type + ' placed'
            } else if (constraintErrors.value[item.id]) {
                return 'INVALID'
            }
            return 'NOT SET'
        }

        function toggleConstraintShown(item) {
            if (constraintsShown.value.includes(item.id)) {
                constraintsShown.value = constraintsShown.value.filter((c) => c !== item.id)
            } else {
                constraintsShown.value = [
                    ...constraintsShown.value,
                    item.id
                ]
            }
        }

        function toggleCurrentPlacement(subject, item) {
            if (currentConstraintPlacement.value) currentConstraintPlacement.value = undefined
            else currentConstraintPlacement.value = getWidgetInfo(subject, item)
        }

        function validateConstraint(cInfo) {
            if (cInfo.type === 'paint' && constraintInfo.value.some((c) => {
                return c.id !== cInfo.id && c.domain === cInfo.domain && c.type === cInfo.type
            })) {
                constraintErrors.value[cInfo.id] = 'Only one paint constraint can exist per domain. Edit the existing paint constraint.'
            } else {
                constraintErrors.value[cInfo.id] = undefined
            }
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
            toggleConstraintShown(constraint)
            selectedProject.value.constraints = [
                ...selectedProject.value.constraints,
                { newAddition: true }
            ]
            changesMade.value = true
        }

        function deleteConstraint(item) {
            allSubjectsForDataset.value.forEach((subject) => {
                setConstraintLocation(subject, item, undefined)
            })
            constraintInfo.value.splice(item.id, 1)
            reassignConstraintIDsByIndex()
            currentConstraintPlacement.value = undefined
            dialogs.value = []
            expandedRows.value = []
            changesMade.value = true
        }

        function submit() {
            const locationData = Object.fromEntries(
                Object.entries(allSetConstraints.value)
                .map(([subjectName, subjectRecords]) => {
                    const subjectID = allSubjectsForDataset.value.find((s) => s.name === subjectName)?.id
                    return [subjectID, Object.fromEntries(
                        Object.entries(subjectRecords).map(([domain, domainRecords]) => {
                            return [domain, convertConstraintDataForDB(Object.values(domainRecords))]
                        })
                    )]
                })
            )

            saveConstraintData(
                selectedProject.value.id,
                locationData
            ).then((response) => {
                if (response.id === selectedProject.value.id) {
                    selectedProject.value = response
                    changesMade.value = false
                }
            })
        }

        watch(allSetConstraints, () => changesMade.value = true, {deep: true})

        return {
            headers,
            changesMade,
            dialogs,
            constraintErrors,
            expandedRows,
            constraintInfo,
            constraintsShown,
            anatomies,
            allSubjectsForDataset,
            constraintPaintRadius,
            constraintPaintExclusion,
            currentConstraintPlacement,
            isShapeShown,
            toggleSubjectShown,
            getPlacementStatus,
            validateConstraint,
            toggleConstraintShown,
            toggleCurrentPlacement,
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
                         <template v-slot:item.show="{ index, item }">
                            <v-icon @click="toggleConstraintShown(item)">
                                {{ constraintsShown.includes(item.id) ? 'mdi-eye-outline' : 'mdi-eye-off-outline' }}
                            </v-icon>
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.type="{ index, item }">
                            <v-select
                                v-model="item.type"
                                :items="['plane', 'paint']"
                                :disabled="item.num_set > 0"
                                :error-messages="constraintErrors[item.id]"
                                @change="(v) => validateConstraint(item)"
                                style="width: 250px"
                            />
                        </template>
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.domain="{ index, item }">
                            <v-select
                                v-model="item.domain"
                                :items="anatomies.map((a) => a.replace('anatomy_', ''))"
                                :disabled="item.num_set > 0"
                                @change="(v) => validateConstraint(item)"
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
                            <div style="width: calc(100% - 20px)">
                                <div
                                    v-for="subject in allSubjectsForDataset"
                                    :key="subject.id"
                                    class="d-flex py-1"
                                    style="align-items: center; justify-content: space-between; width: 100%"
                                >
                                    <span style="width: 150px;">{{ subject.name }}</span>
                                    <v-btn
                                        small
                                        v-if="!currentConstraintPlacement"
                                        @click="toggleSubjectShown(subject.id, item.domain)"
                                    >
                                        {{ isShapeShown(subject.id, item.domain) ? 'Hide' : 'Show' }} subject
                                    </v-btn>
                                    <div
                                        v-else-if="getPlacementStatus(subject, item) === 'PLACING' && item.type === 'paint'"
                                        style="width: 200px; text-align: center;"
                                    >
                                        <v-text-field
                                            v-model.number="constraintPaintRadius"
                                            label="Brush Size"
                                            type="number"
                                            min="1"
                                            max="15"
                                            style="max-width: 70px; display: inline-block; margin-right: 10px"
                                            @click.stop
                                        />
                                        <v-tooltip top>
                                            <template v-slot:activator="{ on, attrs }">
                                                <div
                                                    v-bind="attrs"
                                                    v-on="on"
                                                    style="max-width: 70px; display: inline-block; margin-right: 10px"
                                                >
                                                    <v-switch v-model="constraintPaintExclusion" label="Exclude" />
                                                </div>
                                            </template>
                                            <span>Enable to paint exclusion area. Disable to erase exclusion area.</span>
                                        </v-tooltip>
                                    </div>
                                    <v-spacer v-else />
                                    <div style="width: 140px; text-align: right;">
                                        <span v-if="getPlacementStatus(subject, item) === 'INVALID'">
                                            INVALID
                                        </span>
                                        <span v-else-if="isShapeShown(subject.id, item.domain) && !constraintsShown.includes(item.id)">
                                            Not visible
                                        </span>
                                        <v-btn
                                            v-else-if="isShapeShown(subject.id, item.domain) && getPlacementStatus(subject, item) !== 'plane placed'"
                                            @click="toggleCurrentPlacement(subject, item)"
                                            small
                                        >
                                            <span v-if="getPlacementStatus(subject, item) === 'NOT SET'">BEGIN PLACEMENT</span>
                                            <span v-if="getPlacementStatus(subject, item) === 'PLACING'">DONE</span>
                                            <span v-if="getPlacementStatus(subject, item) === 'paint placed'">EDIT PAINT</span>
                                        </v-btn>
                                        <span v-else> {{ getPlacementStatus(subject, item) }}</span>
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
    padding-left: 15px;
}
th {
    padding-left: 5px !important;
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
