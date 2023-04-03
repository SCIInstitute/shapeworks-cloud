<script lang="ts">

import { defineComponent } from '@vue/composition-api';
import {
    landmarkInfo, selectedDataset, selectedProject
} from '@/store';


export default defineComponent({
    setup() {
        const headers =  [
            {text: 'ID', value: 'id', width: '15px'},
            {text: '', value: 'color', width: '15px'},
            {text: 'Name', value: 'name', width: '100px'},
            {text: '# set', value: 'num_set', width: '70px'},
            // {text: 'Place', value: 'placement_status'},
            {text: 'Comment', value: 'comment'},
        ];

        function getColorString(rgb: number[]){
            return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`
        }

        return {
            selectedDataset,
            selectedProject,
            headers,
            landmarkInfo,
            getColorString,
        }
    }
})
</script>

<template>
    <div class="pa-3">
        <div class="pa-3">
            View / edit project information
        </div>
        <v-expansion-panels :value="0">
            <v-expansion-panel>
                <v-expansion-panel-header>
                    Landmarks
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-data-table
                        :headers="headers"
                        :items="landmarkInfo"
                        item-key="uid"
                        disable-pagination
                        hide-default-footer
                        dense
                        width="100%"
                    >
                        <!-- eslint-disable-next-line -->
                        <template v-slot:item.color="{ item }">
                            <div class='color-square'
                            :style="{backgroundColor: getColorString(item.color)}" />
                        </template>
                    </v-data-table>
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
    height: 15px;
    width: 15px;
}
</style>
