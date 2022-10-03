<script lang="ts">
import { defineComponent, onMounted } from '@vue/composition-api';
import { getDatasets, getProjectsForDataset } from '@/api/rest'
import {
    allDatasets,
    selectedDataset,
    loadingState,
    selectedDataObjects,
    allProjectsForDataset,
    selectedProject,
} from '../store';
import { Dataset, Project } from '@/types';
import router from '@/router';
import CreateProject from '@/components/CreateProject.vue';

export default defineComponent({
  components: { CreateProject },
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

        async function fetchProjectsForDataset(dataset: Dataset) {
            allProjectsForDataset.value = await getProjectsForDataset(dataset.id);
        }

        async function selectOrDeselectDataset (dataset: Dataset) {
            if(!selectedDataset.value){
                selectedDataset.value = dataset;
                fetchProjectsForDataset(dataset)
            } else {
                selectedDataset.value = undefined;
                selectedDataObjects.value = [];
                await getAllDatasets();
            }
        }

        async function selectOrDeselectProject (project: Project) {
            if(!selectedProject.value){
                selectedProject.value = project;
                router.push({
                    name: 'main',
                    params: {
                        dataset: String(selectedDataset.value?.id),
                        project: String(project.id),
                    }
                });
            } else {selectedProject.value = undefined;
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
            allProjectsForDataset,
            selectedProject,
            selectOrDeselectDataset,
            selectOrDeselectProject,
            loadingState,
        }
    }
})
</script>

<template>
    <div>
        <div
            v-if="!selectedDataset"
            class="flex-container pa-5"
        >
            <v-card v-if="allDatasets.length === 0 && !loadingState" width="100%">
                <v-card-title>No datasets.</v-card-title>
            </v-card>
            <v-card
                v-for="dataset in allDatasets"
                :key="'dataset_'+dataset.id"
                class="selectable-card"
                v-show="!selectedDataset || selectedDataset == dataset"
                :width="selectedDataset == dataset ? '100%' :''"
            >
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
            </v-card>
        </div>
        <div v-else class="flex-container pa-5">
            <div style="width:100%">
                <v-icon @click="() => selectOrDeselectDataset(selectedDataset)">
                    mdi-arrow-left
                </v-icon>
            </div>
            <v-card v-if="allProjectsForDataset.length === 0 && !loadingState" width="100%">
                <v-card-title>No projects.</v-card-title>
            </v-card>
            <v-card
                v-for="project in allProjectsForDataset"
                :key="'project_'+project.id"
                class="selectable-card"
                v-show="!selectedProject || selectedProject == project"
                :width="selectedProject == project ? '100%' :''"
            >
                <div class="text-overline mb-4">
                    PROJECT ({{ project.created.split('T')[0] }})
                    FOR DATASET {{ selectedDataset.id }}
                </div>
                <v-list-item-title class="text-h5 mb-1">
                    Project {{ project.id }}
                </v-list-item-title>
                <v-list-item-subtitle>
                    {{ project.description }}
                </v-list-item-subtitle>
                <v-list-item-subtitle>
                    {{ project.keywords }}
                </v-list-item-subtitle>
                <v-card-actions class="action-buttons">
                <v-btn
                    outlined
                    rounded
                    text
                    @click="() => selectOrDeselectProject(project)"
                >
                    {{ selectedProject ?'Deselect' :'Select' }}
                </v-btn>
                </v-card-actions>
            </v-card>
            <create-project />
        </div>
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
