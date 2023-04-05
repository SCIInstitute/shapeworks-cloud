<script lang="ts">
import { DataObject, Dataset } from '@/types'
import { defineComponent, ref } from '@vue/composition-api'
import DataList from './DataList.vue'
import { selectedDataObjects, allDatasets } from '@/store';
import { subsetDataset } from '@/api/rest';


export default defineComponent({
    components: {
        DataList
    },
    props: {
        targetDataset: {
            type: Object as () => Dataset,
            required: true,
        },
    },
    setup(props, context) {
        const name = ref('')
        const description = ref('')
        const keywords = ref('')

        async function submitForm() {
            const selected = selectedDataObjects.value.map(
                (dataObject: DataObject) => ({
                    id: dataObject.id,
                    subject: dataObject.subject,
                    type: dataObject.type,
                })
            )
            const newDataset = await subsetDataset(
                props.targetDataset.id,
                {
                    name: name.value,
                    description: description.value,
                    keywords: keywords.value,
                    selected,
                }
            )
            if(newDataset){
                allDatasets.value.push(newDataset)
                context.emit('close')
            }
        }

        return {
            name,
            description,
            keywords,
            submitForm,
            selectedDataObjects,
        }
    }
})
</script>

<template>
    <div class="px-3 pt-10" style="position: relative">
        <div class="submitButton">
            <div class="text-overline mb-4">
                CREATE NEW DATASET FROM SUBSET OF {{targetDataset.name}}
            </div>
            <v-btn
                class="mt-3"
                color="primary"
                :disabled="name === '' || selectedDataObjects.length === 0"
                @click="submitForm"
            >
                Create subset
            </v-btn>
        </div>
        <v-text-field autofocus label="Subset name" v-model="name" />
        <v-text-field label="Description" v-model="description" />
        <v-text-field label="Keywords" v-model="keywords" />
        Select anatomies and subjects from {{targetDataset.name}} to include in new dataset:
        <data-list
            autoSelectAll
            :dataset="targetDataset.id"
        />
    </div>
</template>

<style>
.submitButton {
    position: absolute!important;
    top: -35px;
    right: 15px;
    display: flex;
    width: calc(100% - 60px);
    column-gap: 20px;
}
</style>
