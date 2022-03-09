<script lang="ts">
import { defineComponent, onMounted } from '@vue/composition-api';
import { getDatasets } from '@/api/rest'
import {
    allDatasets,
    selectedDataset,
    allSubjectsForDataset,
    loadingState,
    selectedDataObjects,
} from '../store';
import { Dataset } from '@/types';
import router from '@/router';

export default defineComponent({
    setup() {
        async function getAllDatasets(){
            loadingState.value = true;
            allDatasets.value = (await getDatasets()).sort((a, b) => {
                if(a.created < b.created) return 1;
                if(a.created > b.created) return -1;
                return 0;
            });
            loadingState.value = false;
        }


        async function selectOrDeselectDataset (dataset: Dataset) {
            if(!selectedDataset.value){
                selectedDataset.value = dataset;
                router.push({
                    name: 'data',
                    params: {
                        dataset: String(selectedDataset.value.id),
                    }
                });
            } else {
                selectedDataset.value = undefined;
                allSubjectsForDataset.value = [];
                selectedDataObjects.value = [];
                await getAllDatasets();
            }
        }

        onMounted(async () => {
            await getAllDatasets();
            if(selectedDataset.value){
                const datasetId = selectedDataset.value.id;
                // reset selectedDataset to maintain updates from latest fetch of all datasets
                selectedDataset.value = allDatasets.value.find(
                    (d) => d.id == datasetId
                )
            }
        })

        return {
            allDatasets,
            selectedDataset,
            selectOrDeselectDataset,
            allSubjectsForDataset,
            loadingState,
        }
    }
})
</script>

<template>
    <div class="flex-container pa-5">
        <v-card v-if="allDatasets.length === 0 && !loadingState" width="100%">
            <v-card-title>No datasets.</v-card-title>
        </v-card>
        <v-card
            v-for="dataset in allDatasets"
            :key="'dataset_'+dataset.id"
            v-show="!selectedDataset || selectedDataset == dataset"
            class="selectable-card"
            :width="selectedDataset == dataset ? '100%' :''"
        >
            <div v-show="!selectedDataset || selectedDataset == dataset">
                <div class="text-overline mb-4">
                    DATASET ({{ dataset.created.split('T')[0] }})
                </div>
                <v-list-item-title class="text-h5 mb-1">
                    {{ dataset.name }}
                </v-list-item-title>
                <v-list-item-subtitle>
                    {{ dataset.description }}
                </v-list-item-subtitle>
                <v-card-actions class="action-buttons">
                <v-btn
                    outlined
                    rounded
                    text
                    @click="() => selectOrDeselectDataset(dataset)"
                >
                    {{ selectedDataset ?'Deselect' :'Select' }}
                </v-btn>
                </v-card-actions>
            </div>
        </v-card>
    </div>
</template>

<style scoped>
.flex-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: stretch;
    column-gap: 15px;
    row-gap: 15px;
    overflow: auto;
}
.selectable-card{
    width: 275px;
    padding: 10px 20px 60px 20px;
}
.action-buttons {
    position: absolute;
    bottom: 10px;
    left: 5px
}
.v-list-item__title, .v-list-item__subtitle {
    white-space: normal!important;
}
</style>
