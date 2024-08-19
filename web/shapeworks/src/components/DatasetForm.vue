<script>
import { ref } from 'vue';
import { createDataset } from '../api/rest'
import {
    loadingState,
    getAllDatasets,
} from '@/store';

export default {
  setup() {
    const creating = ref(false)
    const name = ref('My Dataset')
    const description = ref('')
    const keywords = ref('')
    const license = ref('No license')
    const acknowledgement = ref('No acknowledgement')

    function reset() {
        creating.value = false
        description.value = ''
        keywords.value = ''
    }

    function cancel() {
        creating.value = false;
    }

    // TODO: revise for dataset
    function submit(e) {
        e.preventDefault()
        loadingState.value = true

        const formData = {
            name: name.value,
            description: description.value,
            keywords: keywords.value,
            license: license.value,
            acknowledgement: acknowledgement.value,
        };

        let submitFunction = async () => {
           return await createDataset(formData);
        }

        submitFunction().then(async (response) => {
            // if(response.status === 201){
            //     loadProjectsForDataset(selectedDataset.value.id);
            // } else if (response.status === 200) {
            //     loadProjectsForDataset(selectedDataset.value.id);
            //     editingProject.value = undefined;
            // }
            if (response.status === 201) {
                console.log("SUCCESS")
                await getAllDatasets();
            } else if (response.status === 200) {
                console.log("SUCCESS edit?")
                await getAllDatasets();
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
        loadingState,
        description,
        keywords,
        cancel,
        submit,
    }
  }
}
</script>

<template>
    <div>
    <v-btn
        v-if="!creating"
        class="new-button"
        @click.stop="creating = true"
    >
        + New Dataset
    </v-btn>
    <v-card
        v-else
        class="selectable-card"
        @click.stop
        :ripple="false"
    >
        <div class="text-overline mb-4">
            NEW DATASET
        </div>

        <form :submit="submit">
            <v-text-field autofocus v-model="name" class="text-h5 mb-1" required />
            <v-text-field label="Description" v-model="description" required />
            <v-text-field label="Keywords" v-model="keywords" />
            <v-file-input
                label="Dataset file (.zip)"
                accept=".zip"
            ></v-file-input>
            <v-card-actions class="action-buttons">
                <v-btn
                    outlined
                    rounded
                    text
                    type="submit"
                    @click.stop="submit"
                >
                    Create
                </v-btn>
                <v-btn
                    outlined
                    rounded
                    text
                    @click.stop="cancel"
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
