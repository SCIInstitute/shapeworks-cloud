<script lang="ts">
import { onMounted, ref, watch } from 'vue';
import {
    allDatasets,
    selectedDataset,
    loadingState,
    selectedDataObjects,
    loadProjectsForDataset,
    getAllDatasets,
} from '@/store';
import { Dataset } from '@/types';
import SubsetSelection from '@/components/SubsetSelection.vue';
import router from '@/router';

export default {
  components: { SubsetSelection },
  props: {
    searchText: {
        type: String,
        required: false
    }
  },
    setup(props) {
        const selectingSubsetOf = ref();
        selectedDataset.value = undefined;

        async function selectOrDeselectDataset (dataset: Dataset | undefined) {
            if(!selectedDataset.value && dataset) {
                selectedDataset.value = dataset;

                router.push("/dataset/"+dataset.id);
                loadProjectsForDataset(dataset.id);
            } else {
                selectedDataset.value = undefined;
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

        watch(() => props, () => {
            getAllDatasets();
            selectedDataset.value = undefined;
        }, {deep:true});

        return {
            allDatasets,
            selectedDataset,
            selectOrDeselectDataset,
            selectingSubsetOf,
            loadingState,
        }
    }
}
</script>

<template>
    <div>
        <div
            v-if="!selectedDataset"
            class="flex-container pa-5"
            :style="selectingSubsetOf ? 'width: calc(100% - 500px)' : ''"
        >
            <v-card v-if="allDatasets.length === 0 && !loadingState" width="100%">
                <v-card-title>No datasets.</v-card-title>
            </v-card>
            <v-card
                v-for="dataset in allDatasets"
                :key="'dataset_'+dataset.id"
                :class="dataset.thumbnail? 'selectable-card with-thumbnail': 'selectable-card'"
                v-show="!selectedDataset || selectedDataset == dataset"
                :width="selectedDataset == dataset ? '100%' :''"
                @click="() => selectOrDeselectDataset(dataset)"
            >
                <div class="text-overline mb-4">
                    DATASET ({{ dataset.created ? dataset.created.split('T')[0] : 'No creation time' }})
                    <span v-if="dataset.private" class="red--text">
                        (PRIVATE)
                    </span>
                </div>
                <div class="card-contents">
                    <div>
                        <v-list-item-title class="text-h5 mb-1">
                            {{ dataset.name }}
                        </v-list-item-title>
                        <v-list-item-subtitle>
                            {{ dataset.description }}
                        </v-list-item-subtitle>
                        <div class="text-overline">
                            {{ dataset.summary }}
                        </div>
                        <v-list-item-subtitle v-if="dataset.keywords">
                            <v-chip small v-for="keyword in dataset.keywords.split(',')" :key="keyword">
                                <i>{{ keyword }}</i>
                            </v-chip>
                        </v-list-item-subtitle>
                    </div>
                    <div v-if="dataset.thumbnail">
                        <v-img :src="dataset.thumbnail" width="100"/>
                    </div>
                </div>

                <v-card-actions class="action-buttons">
                <v-btn
                    outlined
                    rounded
                    text
                    @click.stop="() => selectOrDeselectDataset(dataset)"
                >
                    {{ selectedDataset ?'Deselect' :'Select' }}
                </v-btn>
                <v-btn
                    outlined
                    rounded
                    text
                    @click.stop="() => selectingSubsetOf = dataset"
                >
                    Create subset
                </v-btn>
                </v-card-actions>
            </v-card>
        </div>
        <v-navigation-drawer
            right
            absolute
            width="500px"
            :value="selectingSubsetOf !== undefined && !selectedDataset"
        >
             <v-btn
                icon
                @click.stop="selectingSubsetOf = undefined"
                class="pa-3 pt-8"
            >
                <v-icon>mdi-close</v-icon>
            </v-btn>
            <subset-selection
                :targetDataset="selectingSubsetOf"
                v-if="selectingSubsetOf"
                @close="selectingSubsetOf = undefined"
            />
        </v-navigation-drawer>
    </div>
</template>

<style>
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
    padding: 10px 20px 100px 20px;
}
.card-contents {
    display: flex;
    justify-content: space-between;
}
.card-contents {
    overflow-wrap: anywhere;
}
.selectable-card.with-thumbnail {
    width: 375px;
}
.action-buttons {
    position: absolute;
    bottom: 10px;
    left: 5px;
    width: calc(100% - 10px);
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    flex-wrap: wrap;
}
.v-list-item__title, .v-list-item__subtitle {
    white-space: normal!important;
}
</style>
