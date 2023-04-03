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
} from '@/store';
import { Dataset, Project } from '@/types';
import router from '@/router';
import CreateProject from '@/components/CreateProject.vue';
import SubsetSelection from '@/components/SubsetSelection.vue';

export default defineComponent({
  components: { CreateProject, SubsetSelection },
    setup() {
        const deleting = ref();
        const selectingSubsetOf = ref();

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
            deleteProject(deleting.value.id).then(
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
            selectingSubsetOf,
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
            >
                <div class="text-overline mb-4">
                    DATASET ({{ dataset.created ? dataset.created.split('T')[0] : 'No creation time' }})
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
                    @click="() => selectOrDeselectDataset(dataset)"
                >
                    {{ selectedDataset ?'Deselect' :'Select' }}
                </v-btn>
                <v-btn
                    outlined
                    rounded
                    text
                    @click="() => selectingSubsetOf = dataset"
                >
                    Create subset
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
                :class="project.thumbnail? 'selectable-card with-thumbnail': 'selectable-card'"
                v-show="!selectedProject || selectedProject == project"
                :width="selectedProject == project ? '100%' :''"
            >
                <div class="text-overline mb-4">
                    PROJECT ({{ project.created ? project.created.split('T')[0] : 'No creation time'}})
                    FOR DATASET {{ selectedDataset.id }}
                </div>
                <div class="card-contents">
                    <div>
                        <v-list-item-title class="text-h5 mb-1">
                            Project {{ project.id }}
                        </v-list-item-title>
                        <v-list-item-subtitle>
                            {{ project.description }}
                        </v-list-item-subtitle>
                        <v-list-item-subtitle>
                            <i>{{ project.keywords }}</i>
                        </v-list-item-subtitle>
                    </div>
                    <div v-if="project.thumbnail">
                        <v-img :src="project.thumbnail" width="100"/>
                    </div>
                </div>
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
                    @click="deleting = project"
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
            <v-card v-if="deleting">
                <v-card-title class="text-h5">
                Confirmation
                </v-card-title>

                <v-card-text>
                Are you sure you want to delete project {{deleting.id}}
                with description "{{ deleting.description }}"?
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
    padding: 10px 20px 70px 20px;
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
}
.v-list-item__title, .v-list-item__subtitle {
    white-space: normal!important;
}
</style>
