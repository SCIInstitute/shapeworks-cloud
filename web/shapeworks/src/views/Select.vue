<script lang="ts">
import { defineComponent, onMounted } from '@vue/composition-api';
import { getDatasets } from '@/api/rest'
import { allDatasets, selectedDataset } from '../store/index';
import { Dataset } from '@/types';
import router from '@/router/routes';

export default defineComponent({
    setup() {
        onMounted(async () => {
            allDatasets.value = await getDatasets();
        })
        function selectDataset (dataset: Dataset) {
            selectedDataset.value = dataset;
            router.push('data')
        }

        return {
            allDatasets,
            selectedDataset,
            selectDataset,
        }
    }
})
</script>

<template>
  <div class="flex-container pa-5">
    <v-card
        v-for="dataset in allDatasets"
        :key="dataset.id"
        class="dataset-card"
    >
        <div class="text-overline mb-4">
            DATASET {{ dataset.id }}
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
            @click="selectDataset"
        >
            Select
        </v-btn>
        </v-card-actions>
    </v-card>
  </div>
</template>

<style scoped>
.flex-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-around;
    column-gap: 15px;
    row-gap: 15px;
    overflow: auto;
}
.dataset-card{
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
