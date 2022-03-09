<script lang="ts">
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';

import imageReader from '../reader/image';
import { getDataObjectsForSubject } from '@/api/rest';
import { defineComponent, onMounted, ref, watch } from '@vue/composition-api';
import { DataObject, ShapeData, Subject } from '../types';
import { getSubjectsForDataset } from '@/api/rest'
import ShapeViewer from '../components/ShapeViewer.vue';
import {
    selectedDataset,
    allSubjectsForDataset,
    loadDataset,
    allDataObjectsInDataset,
    selectedDataObjects,
    loadingState,
} from '../store';
import router from '@/router';


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
        async function fetchData(datasetId: number) {
            loadingState.value = true;
            allSubjectsForDataset.value = (await getSubjectsForDataset(datasetId)).sort((a, b) => {
                if(a.created < b.created) return 1;
                if(a.created > b.created) return -1;
                return 0;
            });
            allDataObjectsInDataset.value =  (await Promise.all(allSubjectsForDataset.value.map(
                async (subject: Subject) => (await getDataObjectsForSubject(subject.id)).map(
                    (dataObject: DataObject) => Object.assign(dataObject, {subject})
                ))
            )).flat()
            loadingState.value = false;
        }

        function setTableHeaders() {
            headers.value = [
                {text: 'ID', sortable: true, value: 'id'},
                {text: 'Type', sortable: true, value: 'type'},
                {text: 'Subject', value: 'subject'},
                {text: 'File Name', sortable: true, value: 'file', cellClass: 'file-column'},

            ]
            if(selectedDataObjects.value.length > 0){
                headers.value.push(
                    {text: 'Display', sortable: true, value: 'display'}
                )
            }
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
            setTableHeaders();
        })

        const mini = ref(false);
        const search = ref('');
        const headers = ref()
        const rows = ref<number>(1);
        const cols = ref<number>(1);
        const renderData = ref<ShapeData[]>([]);

        function shortFileName(file: string) {
            const split = file.split('?')[0].split('/')
            return split[split.length-1]
        }

        function shortDateString(date: string) {
            return date.split('T')[0]
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

        watch(selectedDataObjects, async (currentValue, oldValue) => {
            renderData.value = []
            renderData.value = (await Promise.all(selectedDataObjects.value.map(
                (dataObject) => imageReader(
                    dataObject.file,
                    shortFileName(dataObject.file)
                )
            ))).map(
                (shape) => ({ shape, points: vtkPolyData.newInstance() })
            );
            const n = renderData.value.length;
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
                setTableHeaders();
            }
        })

        return {
            mini,
            search,
            headers,
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
                    <div>
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
                            show-select
                            dense
                        >
                            <!-- eslint-disable-next-line -->
                            <template v-slot:group.header="{ group, headers, toggle, isOpen }">
                            <td :colspan="headers.length">
                                <v-btn @click="toggle" x-small icon :ref="group">
                                    <v-icon v-if="isOpen">mdi-plus</v-icon>
                                    <v-icon v-else>mdi-minus</v-icon>
                                </v-btn>
                                <v-tooltip bottom>
                                <template v-slot:activator="{ on, attrs }">
                                    <span
                                        class="mx-5 font-weight-bold"
                                        v-bind="attrs"
                                        v-on="on"
                                    >
                                        Subject: {{ group.name }}
                                    </span>
                                </template>
                                <span>ID: {{ group.id }} | Created: {{ shortDateString(group.created) }} | Modified: {{ shortDateString(group.modified) }}</span>
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
    max-width: 40px!important;
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
