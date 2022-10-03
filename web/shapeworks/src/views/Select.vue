<script lang="ts">
import { defineComponent, onMounted, ref } from '@vue/composition-api';
import { getDatasets, getProjectsForDataset, deleteProject, } from '@/api/rest'
import {
    allDatasets,
    selectedDataset,
    loadingState,
    selectedDataObjects,
    allProjectsForDataset,
    loadProjectForDataset,
    selectedProject,
} from '../store';
import { Dataset, Project } from '@/types';
import router from '@/router';
import CreateProject from '@/components/CreateProject.vue';

export default defineComponent({
  components: { CreateProject },
    setup() {
        const deleting = ref();

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

        function deleteProj() {
            loadingState.value = true
            deleteProject(deleting.value).then(
                () => {
                    deleting.value = undefined
                    if(selectedDataset.value){
                        loadProjectForDataset(undefined, selectedDataset.value.id)
                    }
                    loadingState.value = false
                }
            )
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
            deleting,
            deleteProj,
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
                    <i>{{ project.keywords }}</i>
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
                <v-btn
                    outlined
                    rounded
                    text
                    color="red"
                    @click="deleting = project.id"
                >
                    Delete
                </v-btn>
                </v-card-actions>
            </v-card>
            <create-project />
            <v-dialog
                :value="deleting"
                width="500"
            >
            <v-card>
                <v-card-title class="text-h5">
                Confirmation
                </v-card-title>

                <v-card-text>
                Are you sure you want to delete project {{deleting}}?
                </v-card-text>

                <v-divider></v-divider>

                <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                    text
                    @click="deleting = undefined"
                >
                    Cancel
                </v-btn>
                <v-btn
                    text
                    color="red"
                    @click="deleteProj"
                >
                    Delete
                </v-btn>
                </v-card-actions>
            </v-card>
            </v-dialog>
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
    left: 5px;
    width: calc(100% - 10px);
    display: flex;
    justify-content: space-between;
}
.v-list-item__title, .v-list-item__subtitle {
    white-space: normal!important;
}
</style>
