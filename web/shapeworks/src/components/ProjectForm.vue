<script>
import { defineComponent, ref } from 'vue';
import { createProject, editProject } from '../api/rest'
import {
    selectedDataset,
    loadingState,
    editingProject,
    loadProjectsForDataset,
} from '@/store';

export default defineComponent({
  props: {
    editMode: {
        type: Boolean,
        default: false
    },
  },
  setup(props, { emit }) {
    const creating = ref(false)
    const name = ref('My Project')
    const description = ref('')
    const keywords = ref('')
    const privated = ref(false);
    const readonly = ref(false);

    function reset() {
        creating.value = false
        description.value = ''
        keywords.value = ''
    }

    function cancel() {
        if(props.editMode) {
            emit('cancel')
        } else {
            creating.value = false
        }
    }

    function submit(e) {
        e.preventDefault()
        loadingState.value = true

        const formData = {
            name: name.value,
            private: privated.value,
            dataset: selectedDataset.value.id,
            description: description.value,
            keywords: keywords.value,
            readonly: readonly.value,
        };

        let submitFunction = async () => {
           return await createProject(formData);
        }

        if (props.editMode) {
            submitFunction = async () => {
                return await editProject(editingProject.value.id, formData);
            }
        }

        submitFunction().then(async (response) => {
            if(response.status === 201){
                loadProjectsForDataset(selectedDataset.value.id);
            } else if (response.status === 200) {
                loadProjectsForDataset(selectedDataset.value.id);
                editingProject.value = undefined;
            }

            loadingState.value = false
            reset()
        }).catch((error) => {
            console.log(error)
            loadingState.value = false
        })
    }

    if (props.editMode) {
        name.value = editingProject.value.name;
        description.value = editingProject.value.description;
        keywords.value = editingProject.value.keywords;
        privated.value = editingProject.value.private;
        readonly.value = editingProject.value.readonly;
    }

    return {
        creating,
        name,
        selectedDataset,
        loadingState,
        description,
        keywords,
        privated,
        readonly,
        editingProject,
        cancel,
        submit,
    }
  }
})
</script>

<template>
    <div>
    <v-btn
        v-if="!creating && !editMode"
        class="new-button"
        @click="creating = true"
    >
        + New Project
    </v-btn>
    <v-card
        v-else
        class="selectable-card"
    >
        <div v-if="!editMode" class="text-overline mb-4">
            NEW PROJECT FOR DATASET {{selectedDataset.id}}
        </div>

        <form :submit="submit">
            <v-text-field autofocus v-model="name" class="text-h5 mb-1"/>
            <v-text-field label="Description" v-model="description" />
            <v-text-field label="Keywords" v-model="keywords" />
            <v-checkbox dense label="Make this project read only" v-model="readonly" />
            <v-checkbox  dense v-if="creating" label="Make this project private" v-model="privated" />
            <v-card-actions class="action-buttons">
                <v-btn
                    outlined
                    rounded
                    text
                    type="submit"
                    @click="submit"
                >
                    {{ (editMode) ? "Save" : "Create" }}
                </v-btn>
                <v-btn
                    outlined
                    rounded
                    text
                    @click="cancel"
                >
                    Cancel
                </v-btn>
            </v-card-actions>
        </form>
    </v-card>
    </div>
</template>

<style scoped>
.new-button {
    height: 100%!important;
    width: 150px;
}
</style>
