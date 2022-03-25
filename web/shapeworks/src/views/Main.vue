<script lang="ts">
import imageReader from '../reader/image';
import { groupBy, shortFileName } from '../helper';
import { defineComponent, onMounted, ref, watch } from '@vue/composition-api';
import { DataObject, ShapeData } from '../types';
import ShapeViewer from '../components/ShapeViewer.vue';
import DataList from '../components/DataList.vue'
import {
    selectedDataset,
    allSubjectsForDataset,
    selectedDataObjects,
    loadDataset,
} from '../store';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import router from '@/router';


export default defineComponent({
    components: {
        ShapeViewer,
        DataList,
    },
    props: {
        dataset: {
            type: Number,
            required: true,
        },
    },
    setup(props) {
        const mini = ref(false);
        const tab = ref();
        const rows = ref<number>(1);
        const cols = ref<number>(1);
        const renderData = ref<Record<string, ShapeData[]>>({});

        onMounted(async () => {
            await loadDataset(props.dataset);
        })

        function toSelectPage(){
            selectedDataset.value = undefined;
            router.push({
                name: 'select',
            });
        }

        watch(selectedDataObjects, async () => {
            renderData.value = {}
            const groupedSelections: Record<string, DataObject[]> = groupBy(selectedDataObjects.value, 'subject')
            renderData.value = Object.fromEntries(
                await Promise.all(Object.entries(groupedSelections).map(
                    async ([subjectId, dataObjects]) => {
                        let subjectName = subjectId;
                        if(allSubjectsForDataset.value){
                            const subject = allSubjectsForDataset.value.find(
                                (subject) => subject.id.toString() === subjectId
                            )
                            if (subject) subjectName = subject.name
                        }
                        const shapeDatas = (await Promise.all(dataObjects.map(
                            (dataObject) => imageReader(
                                dataObject.file,
                                shortFileName(dataObject.file)
                            )
                        ))).map((imageData) => ({shape: imageData, points: vtkPolyData.newInstance()}))
                        return [
                            subjectName, shapeDatas
                        ]
                    }
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
        })

        return {
            mini,
            tab,
            rows,
            cols,
            renderData,
            selectedDataset,
            selectedDataObjects,
            toSelectPage,
        }
    }
})
</script>


<template>
    <div class='content-area' style='height: 100%'>
        <v-navigation-drawer :mini-variant.sync="mini" width="650" absolute>
                <v-list-item>
                    <v-btn
                        icon
                        @click.stop="mini=!mini"
                        class="mr-3"
                    >
                        <v-icon large>mdi-menu</v-icon>
                    </v-btn>
                    <v-list-item-title class="text-h6">
                        Dataset: {{ selectedDataset.name }}
                        <v-tooltip bottom>
                        <template v-slot:activator="{ on, attrs }">
                            <v-icon
                            dark
                            v-bind="attrs"
                            v-on="on"
                            @click="toSelectPage"
                            >
                            mdi-close
                            </v-icon>
                        </template>
                        <span>Return to dataset selection</span>
                        </v-tooltip>
                    </v-list-item-title>
                    <v-btn
                        icon
                        @click.stop="mini=!mini"
                        class="pr-3"
                    >
                        <v-icon large>mdi-chevron-left</v-icon>
                    </v-btn>
                </v-list-item>
                <v-list-item>
                    <v-icon />
                    <v-tabs v-model="tab" fixed-tabs>
                        <v-tab href="#data">Data</v-tab>
                        <v-tab-item value="data">
                            <DataList :dataset="dataset"/>
                        </v-tab-item>
                        <v-tab href="#groom">Groom</v-tab>
                        <v-tab-item value="groom">
                            Groom
                        </v-tab-item>
                        <v-tab href="#optimize">Optimize</v-tab>
                        <v-tab-item value="optimize">
                            Optimize
                        </v-tab-item>
                        <v-tab href="#analyze">Analyze</v-tab>
                        <v-tab-item value="analyze">
                            Analyze
                        </v-tab-item>
                    </v-tabs>
                </v-list-item>
                <br>
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
            </template>
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
</style>