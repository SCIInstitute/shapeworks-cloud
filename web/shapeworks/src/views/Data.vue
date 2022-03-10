<script lang="ts">
import imageReader from '../reader/image';
import { groupBy, shortDateString, shortFileName } from '../helper';
import { getDataObjectsForSubject } from '@/api/rest';
import { defineComponent, onMounted, ref, watch } from '@vue/composition-api';
import { DataObject, ShapeData, Subject } from '../types';
import { getSubjectsForDataset } from '@/api/rest'
import ShapeViewer from '../components/ShapeViewer.vue';
import {
    selectedDataset,
    loadDataset,
    allDataObjectsInDataset,
    selectedDataObjects,
    loadingState,
} from '../store';
import router from '@/router';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';


export default defineComponent({
    components: {
        ShapeViewer,
    },
    props: {
        dataset: {
            type: Number,
            required: true,
        },
    },
    setup(props) {
        const mini = ref(false);
        const search = ref('');
        const subjects = ref<Record<string, Subject>>({})
        const rows = ref<number>(1);
        const cols = ref<number>(1);
        const renderData = ref<Record<string, ShapeData[]>>({});
        const headers =  [
            {text: 'ID', sortable: true, value: 'id'},
            {text: 'Type', sortable: true, value: 'type'},
            {text: 'Subject', value: 'subject'},
            {text: 'File Name', sortable: true, value: 'file', cellClass: 'file-column'},
        ];

        async function fetchData(datasetId: number) {
            loadingState.value = true;
            subjects.value = Object.fromEntries((await getSubjectsForDataset(datasetId)).sort((a, b) => {
                if(a.created < b.created) return 1;
                if(a.created > b.created) return -1;
                return 0;
            }).map((subject: Subject) => [subject.id, subject]));
            allDataObjectsInDataset.value =  (await Promise.all(
                Object.values(subjects.value).map(
                    async (subject: Subject) => await getDataObjectsForSubject(subject.id)
                )
            )).flat()
            loadingState.value = false;
        }

        function displayLocation(id: number){
            const selectedObjectIds = selectedDataObjects.value.map((obj) => obj.id)
            if(selectedObjectIds.includes(id)){
                const index = selectedObjectIds.indexOf(id);
                const i = index % cols.value;
                const j = Math.floor(index / cols.value)

                return "ABCDE".charAt(i)+(j+1).toString();
            }
            return '';
        }

        function updateDisplayLocations() {
            allDataObjectsInDataset.value = allDataObjectsInDataset.value.map(
                (obj) => Object.assign(obj, {'display': displayLocation(obj.id)})
            )
        }

        onMounted(async () => {
            await loadDataset(props.dataset);
            if(!selectedDataset.value) {
                router.push({
                    name: 'select',
                });
                return;
            }
            await fetchData(selectedDataset.value.id)
        })

        watch(selectedDataObjects, async (currentValue, oldValue) => {
            renderData.value = {}
            const groupedSelections: Record<string, DataObject[]> = groupBy(selectedDataObjects.value, 'subject')
            renderData.value = Object.fromEntries(
                await Promise.all(Object.entries(groupedSelections).map(
                    async ([subjectId, dataObjects]) => [
                        subjects.value[subjectId].name,
                        (await Promise.all(dataObjects.map(
                            (dataObject) => imageReader(
                                dataObject.file,
                                shortFileName(dataObject.file)
                            )
                        ))).map((imageData) => ({shape: imageData, points: vtkPolyData.newInstance()}))
                    ]
                )
            ))

            const n = Object.keys(renderData.value).length;
            const sqrt = Math.ceil(Math.sqrt(n));
            if(sqrt <= 5) {
                rows.value = Math.ceil(n / sqrt);
                cols.value = sqrt;
            } else {
                rows.value = Math.ceil(n / 5);
                cols.value = 5;
            }
            if(currentValue.length !== oldValue.length){
                updateDisplayLocations();
            }
        })

        return {
            mini,
            search,
            headers,
            subjects,
            rows,
            cols,
            renderData,
            selectedDataset,
            allDataObjectsInDataset,
            selectedDataObjects,
            shortFileName,
            shortDateString,
        }
    }
})
</script>


<template>
    <div style="height: 100%">
        <div class="context-card">
            <div>
                <div class="text-overline">
                    DATASET ({{ selectedDataset.created.split('T')[0] }})
                </div>
                <v-list-item-title class="text-h6 mb-1">
                    {{ selectedDataset.name }}
                </v-list-item-title>
            </div>
        </div>
        <v-divider />

        <div class='content-area'>
            <v-navigation-drawer :mini-variant.sync="mini" width="650" absolute>
                <v-list-item>
                    <v-btn
                        icon
                        @click.stop="mini=false"
                        class="pr-3"
                    >
                    <v-icon large>mdi-database</v-icon>
                    </v-btn>
                    <v-list-item-title class="text-h6">
                        Data Objects
                    </v-list-item-title>
                    <v-btn
                        icon
                        v-if="!mini"
                        @click.stop="mini=true"
                    >
                    <v-icon large>mdi-chevron-left</v-icon>
                    </v-btn>
                </v-list-item>
                <v-list-item>
                    <v-icon />
                    <div style="width:100%">
                        <v-text-field
                            v-model="search"
                            append-icon="mdi-magnify"
                            label="Search"
                            single-line
                            hide-details
                            class="pa-5"
                        ></v-text-field>
                        <v-data-table
                            v-model="selectedDataObjects"
                            :headers="headers"
                            :items="allDataObjectsInDataset"
                            :search="search"
                            group-by="subject"
                            disable-pagination
                            hide-default-footer
                            show-select
                            dense
                            width="100%"
                        >
                            <!-- eslint-disable-next-line -->
                            <template v-slot:group.header="{ group, headers, toggle, isOpen }">
                                <td :colspan="headers.length">
                                    <v-tooltip bottom>
                                    <template v-slot:activator="{ on, attrs }">
                                        <span
                                            class="font-weight-bold"
                                            v-bind="attrs"
                                            v-on="on"
                                        >
                                            Subject: {{ subjects[group].name }}
                                        </span>
                                    </template>
                                    <span>
                                        ID: {{ subjects[group].id }} |
                                        Created: {{ shortDateString(subjects[group].created) }} |
                                        Modified: {{ shortDateString(subjects[group].modified) }}
                                    </span>
                                    </v-tooltip>
                                </td>
                            </template>
                            <!-- eslint-disable-next-line -->
                            <template v-slot:item.file="{ item }">
                                <span>{{ shortFileName(item.file) }}</span>
                            </template>
                        </v-data-table>
                    </div>
                </v-list-item>
                <br/>
            </v-navigation-drawer>

            <div :class="mini ?'pa-5 render-area maximize' :'pa-5 render-area'">
                <span v-if="selectedDataObjects.length == 0">Select any number of data objects</span>
                <template v-else>
                <shape-viewer
                    :data="renderData"
                    :rows="rows"
                    :columns="cols"
                    :glyph-size="1.5"
                />
                <div class="column-index labels">
                    <div v-for="i in Array(cols).keys()" v-bind:key="i">
                        {{"ABCDE".charAt(i)}}
                    </div>
                </div>
                <div class="row-index labels">
                    <div v-for="j in Array(rows).keys()" v-bind:key="j">
                        {{j+1}}
                    </div>
                </div>
                </template>
            </div>
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
.file-column {
    max-width: 60px!important;
    overflow: hidden;
    text-overflow: ellipsis;
}
.content-area {
    position: relative;
    min-height: calc(100vh - 161px);
}
.render-area {
    position: absolute;
    display: flex;
    justify-content: space-between;
    left: 650px;
    width: calc(100% - 650px);
    height: 100%;
}
.render-area.maximize {
    left: 60px;
    width: calc(100% - 60px);
}
.render-area > * {
    flex-grow: 1;
}
.labels {
    position: absolute;
    display: flex;
    justify-content: space-around;
}
.column-index {
    width: calc(100% - 40px);
    flex-direction: row;
}
.row-index {
    height: calc(100% - 40px);
    flex-direction: column;
}
</style>
