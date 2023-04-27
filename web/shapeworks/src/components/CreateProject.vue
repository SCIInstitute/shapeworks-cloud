<script>
import { defineComponent, ref } from '@vue/composition-api';
import { createProject, getProjectsForDataset } from '../api/rest'
import {
    selectedDataset,
    loadingState,
    allProjectsForDataset,
} from '@/store';

export default defineComponent({
  setup() {
    const creating = ref(false)
    const name = ref('My Project')
    const description = ref('')
    const keywords = ref('')
    const privated = ref(false);

    function reset() {
        creating.value = false
            description.value = ''
            keywords.value = ''
    }

    function create(e) {
        e.preventDefault()
        loadingState.value = true
        createProject({
            name: name.value,
            private: privated.value,
            dataset: selectedDataset.value.id,
            description: description.value,
            keywords: keywords.value,
        }).then(async (response) => {
            if(response.status === 201){
                allProjectsForDataset.value = await getProjectsForDataset(selectedDataset.value.id);
            }
            loadingState.value = false
            reset()
        }).catch((error) => {
            console.log(error)
            loadingState.value = false
        })
    }

    return {
        creating,
        name,
        selectedDataset,
        loadingState,
        description,
        keywords,
        privated,
        create,
    }
  }
})
</script>

<template>
    <div>
    <v-btn
        v-if="!creating"
        class="new-button"
        @click="creating = true"
    >
        + New Project
    </v-btn>
    <v-card
        v-else
        class="selectable-card"
    >
        <div class="text-overline mb-4">
            NEW PROJECT FOR DATASET {{ selectedDataset.id }}
        </div>
        <form :submit="create">
            <v-text-field autofocus v-model="name" class="text-h5 mb-1"/>
            <v-text-field label="Description" v-model="description" />
            <v-text-field label="Keywords" v-model="keywords" />
            <v-checkbox label="Make this project private" v-model="privated" />
            <v-card-actions class="action-buttons">
                <v-btn
                    v-if="description"
                    outlined
                    rounded
                    text
                    type="submit"
                    @click="create"
                >
                    Create
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
