<script lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { cloneProject, deleteProject } from '@/api/rest'
import {
    selectedDataset,
    loadingState,
    allProjectsForDataset,
    selectedProject,
    editingProject,
    selectProject,
    selectedDataObjects,
    getAllDatasets,
    loadDataset,
    loadProjectsForDataset,
    sortAscending,
    sortOption,
    filters,
} from '@/store';
import ProjectForm from '@/components/ProjectForm.vue';
import { Project } from '@/types';
import router from '@/router';

export default {
    components: { ProjectForm },
    props: {
        dataset: {
            type: Number,
            required: true
        },
        searchText: {
            type: String,
            required: false
        }
    },
    setup(props) {
        const deleting = ref();

        const sortedProjects = computed(() => {
            if (allProjectsForDataset.value) {
                let projects = allProjectsForDataset.value.sort((a, b) => {
                    let sortA = a[sortOption.value];
                    let sortB = b[sortOption.value];

                    if ((!sortA || !sortB)) {
                        return 0;
                    }

                    if (sortA < sortB) {
                        return (sortAscending.value === true) ? -1 : 1;
                    }
                    if (sortA > sortB) {
                        return (sortAscending.value === true) ? 1 : -1;
                    }
                    return 0;
                });

                projects = projects.filter((p) => {
                    if (filters.value.private) {
                        return !p.private;
                    }
                    if (filters.value.readonly) {
                        return !p.readonly;
                    }
                    return true;
                })

                return projects;
            }
            return [];
        });

        async function selectOrDeselectProject (project: Project) {
            if(!selectedProject.value){
                selectProject(project.id);
                router.push(`/dataset/${props.dataset}/project/${project.id}`);
            } else {
                selectedProject.value = undefined;
                selectedDataObjects.value = [];
                await getAllDatasets();
            }
        }

        function cloneProj(project: Project) {
            loadingState.value = true
            cloneProject(project.id)
            .then(() => {
                loadProjectsForDataset(props.dataset);
                loadingState.value = false;
            })
        }

        function deleteProj() {
            loadingState.value = true
            deleteProject(deleting.value.id).then(
                () => {
                    deleting.value = undefined
                    loadProjectsForDataset(props.dataset);
                    if(selectedDataset.value){
                        selectedProject.value = undefined;
                    }
                    loadingState.value = false
                }
            )
        }

        function back() {
            selectedDataset.value = undefined;
            router.push("/");
        }

        function updateSelectedDataset() {
            if (selectedDataset.value === undefined
            || selectedDataset.value.id !== props.dataset
            ) {
                loadDataset(props.dataset);
                loadProjectsForDataset(props.dataset);
            }
        }

        onMounted(updateSelectedDataset);

        watch(() => props.dataset, updateSelectedDataset);
        watch(() => props.searchText, () => loadProjectsForDataset(props.dataset));


        return {
            selectedDataset,
            allProjectsForDataset,
            selectedProject,
            selectOrDeselectProject,
            cloneProj,
            deleting,
            deleteProj,
            editingProject,
            selectProject,
            back,
            loadingState,
            sortedProjects,
        }
    }
}
</script>

<template>
    <div>
        <div v-if="selectedDataset" class="flex-container pa-5">
            <div style="width:100%">
                <v-icon @click="back">
                    mdi-arrow-left
                </v-icon>
                {{ selectedDataset.name }}
            </div>
            <v-card v-if="(allProjectsForDataset === undefined || allProjectsForDataset.length === 0) && !loadingState" width="100%">
                <v-card-title>No projects.</v-card-title>
            </v-card>
            <div
                v-for="project in sortedProjects"
                :key="'project_'+project.id"
                @click="() => selectOrDeselectProject(project)"
            >
                <project-form
                    v-if="editingProject === project"
                    editMode
                    @cancel="() => editingProject = undefined"
                />
                <v-card
                    v-else
                    :class="project.thumbnail? 'selectable-card with-thumbnail': 'selectable-card'"
                    v-show="!selectedProject || selectedProject == project"
                    :width="selectedProject == project ? '100%' :''"
                >
                    <div class="text-overline mb-4">
                        PROJECT ({{ project.created ? project.created.split('T')[0] : 'No creation time'}})
                        FOR DATASET {{ selectedDataset.id }}
                        <span v-if="project.readonly" class="blue--text">
                            (READ ONLY)
                        </span>
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
                            outlined rounded text style="width:40%; margin-left: 8px;"
                            @click.stop="() => cloneProj(project)"
                        >
                            Clone
                        </v-btn>
                        <v-btn
                            outlined rounded text style="width:40%"
                            @click.stop="editingProject = project"
                            >
                            Edit
                        </v-btn>
                        <v-btn
                            outlined rounded text style="width:40%"
                            color="blue"
                            @click.stop="() => selectOrDeselectProject(project)"
                        >
                            Select
                        </v-btn>
                        <v-btn
                            outlined rounded text style="width:40%"
                            color="red"
                            @click.stop="deleting = project"
                        >
                            Delete
                        </v-btn>
                    </v-card-actions>
                </v-card>
            </div>
            <!-- Create project form (shows at end of list). Does this need more advanced perms? -->
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
                    @click.stop="deleting = undefined"
                >
                    Cancel
                </v-btn>
                <v-btn
                    text
                    color="red"
                    @click.stop="deleteProj"
                >
                    Delete
                </v-btn>
                </v-card-actions>
            </v-card>
            </v-dialog>
        </div>
    </div>
</template>
