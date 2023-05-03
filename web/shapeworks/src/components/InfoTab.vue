<script>
import pointsReader from '../reader/points';
import { COLORS } from './ShapeViewer/methods'
import { defineComponent, onMounted, ref } from '@vue/composition-api';
import { landmarkColorList, selectedDataset, selectedProject } from '@/store';


// from https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
function hexToRgb(hex) {
  var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? [
    parseInt(result[1], 16),
    parseInt(result[2], 16),
    parseInt(result[3], 16)
   ] : [0, 0, 0];
}

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
        const landmarkInfo = ref();

        onMounted(async () => {
            if (selectedProject.value?.landmarks){
                const subjectParticles = await Promise.all(
                    selectedProject.value.landmarks.map(
                        async (subjectLandmarks) => {
                            const locations = await pointsReader(subjectLandmarks.file)
                            return locations.getPoints().getNumberOfPoints()
                        }
                    )
                )
                if (subjectParticles.length > 0){
                    const numRows = Math.max(...subjectParticles)
                    landmarkInfo.value = [...Array(numRows).keys()].map((index) => {
                        let currentInfo = {
                            id: index,
                            color: COLORS[index % COLORS.length],
                            name: `L${index}`,
                            num_set: subjectParticles.filter(
                                (numLocations) => numLocations > index
                            ).length,
                            comment: undefined,

                        }
                        if (selectedProject.value?.landmarks_info && selectedProject.value.landmarks_info.length > index) {
                            currentInfo = Object.assign(
                                currentInfo,
                                selectedProject.value?.landmarks_info[index]
                            )
                        }
                        if (currentInfo.color.toString().includes("#")) {
                            currentInfo.color = hexToRgb(currentInfo.color.toString())
                        }
                        return currentInfo
                    })
                    updateLandmarkColorList()
                }
            }
        })

        function updateLandmarkColorList() {
            landmarkColorList.value = landmarkInfo.value.map(
                (info) => info.color
            )
        }

        function getColorString(rgb){
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
