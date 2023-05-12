<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { deleteProject } from '@/api/rest'
import {
    selectedDataset,
    loadingState,
    allProjectsForDataset,
    selectedProject,
    editingProject,
    selectProject,
selectedDataObjects,
getAllDatasets,
} from '@/store';
import ProjectForm from '@/components/ProjectForm.vue';
import SubsetSelection from '@/components/SubsetSelection.vue';
import { Project } from '@/types';

export default defineComponent({
  components: { ProjectForm, SubsetSelection },
    setup() {
        const deleting = ref();

        async function selectOrDeselectProject (project: Project) {
            if(!selectedProject.value){
                selectProject(project.id);
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
                        selectedProject.value = undefined;
                    }
                    loadingState.value = false
                }
            )
        }

        return {
            selectedDataset,
            allProjectsForDataset,
            selectedProject,
            selectOrDeselectProject,
            deleting,
            deleteProj,
            editingProject,
            selectProject
        }
    }
})
</script>

<template>
    <div>
        <div v-if="selectedDataset" class="flex-container pa-5">
            <div style="width:100%">
                <v-icon @click="() => selectedDataset = undefined">
                    mdi-arrow-left
                </v-icon>
                {{ selectedDataset.name }}
            </div>
            <v-card v-if="(allProjectsForDataset === undefined || allProjectsForDataset.length === 0) && !loadingState" width="100%">
                <v-card-title>No projects.</v-card-title>
            </v-card>
            <div 
                v-for="project in allProjectsForDataset"
                :key="'project_'+project.id"
            >
            <project-form v-if="editingProject === project" editMode />
                <v-card
                    v-else
                    :class="project.thumbnail? 'selectable-card with-thumbnail': 'selectable-card'"
                    v-show="!selectedProject || selectedProject == project"
                    :width="selectedProject == project ? '100%' :''"
                >
                    <div class="text-overline mb-4">
                        PROJECT ({{ project.created ? project.created.split('T')[0] : 'No creation time'}})
                        FOR DATASET {{ selectedDataset.id }}
                        <span v-if="project.private" class="red--text">
                            (PRIVATE)
                        </span>
                    </div>
                    <div class="card-contents">
                        <div>
                            <v-list-item-title class="text-h5 mb-1">
                                {{ project.name }}
                            </v-list-item-title>
                            <v-list-item-subtitle>
                                {{ project.description }}
                            </v-list-item-subtitle>
                            <v-list-item-subtitle v-if="project.keywords">
                                <v-chip small v-for="keyword in project.keywords.split(',')" :key="keyword">
                                    <i>{{ keyword }}</i>
                                </v-chip>
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
                        Select
                    </v-btn>
                    <v-btn
                        outlined
                        rounded
                        text
                        @click="editingProject = project"
                    >
                        Edit
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
            </div>
            <project-form />
            <v-dialog
                :value="deleting"
                width="500"
            >
            <v-card v-if="deleting">
                <v-card-title class="text-h5">
                Confirmation
                </v-card-title>

                <v-card-text>
                Are you sure you want to delete project "{{ deleting.name }}"?
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