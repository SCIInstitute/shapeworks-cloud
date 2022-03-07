<script lang="ts">
import { getDataObjectsForSubject } from '@/api/rest';
import { defineComponent, onMounted, ref } from '@vue/composition-api';
import {
    selectedDataset,
    selectedSubject,
    loadDatasetAndSubject,
    allDataObjectsForSubject,
    selectedDataObjects,
} from '../store';


export default defineComponent({
    props: {
        dataset: {
            type: Number,
            required: true,
        },
        subject: {
            type: Number,
            required: true,
        },
    },
    setup(props) {
        onMounted(async () => {
            await loadDatasetAndSubject(props.dataset, props.subject);
            if (!selectedSubject.value) return;
            allDataObjectsForSubject.value = await getDataObjectsForSubject(selectedSubject.value.id)
        })

        const mini = ref(false);
        const search = ref('');
        const headers = [
            {text: 'ID', sortable: true, value: 'id'},
            {text: 'Type', sortable: true, value: 'type'},
            {text: 'File Name', sortable: true, value: 'file'},
        ]

        function shortFileName(file: string) {
            const split = file.split('?')[0].split('/')
            return split[split.length-1]
        }

        return {
            mini,
            search,
            headers,
            selectedDataset,
            selectedSubject,
            allDataObjectsForSubject,
            selectedDataObjects,
            shortFileName,
        }
    }
})
</script>


<template>
    <div style="height: 100%">
        <div class="context-card">
            <div>
                <div class="text-overline">
                    DATASET ({{ selectedDataset.created.split('T')[0] }})
                </div>
                <v-list-item-title class="text-h6 mb-1">
                    {{ selectedDataset.name }}
                </v-list-item-title>
            </div>
            <div>
                <div class="text-overline">
                    SUBJECT ({{ selectedSubject.created.split('T')[0] }})
                </div>
                <v-list-item-title class="text-h6 mb-1">
                    {{ selectedSubject.name }}
                </v-list-item-title>
            </div>
        </div>
        <v-divider />

        <div class='content-area'>
            <v-navigation-drawer :mini-variant.sync="mini" width="500" absolute>
                <v-list-item>
                    <v-btn
                        icon
                        @click.stop="mini=false"
                        class="pr-3"
                    >
                    <v-icon large>mdi-database</v-icon>
                    </v-btn>
                    <v-list-item-title class="text-h6">
                        Data Objects
                    </v-list-item-title>
                    <v-btn
                        icon
                        v-if="!mini"
                        @click.stop="mini=true"
                    >
                    <v-icon large>mdi-chevron-left</v-icon>
                    </v-btn>
                </v-list-item>
                <v-list-item>
                    <v-icon />
                    <div>
                        <v-text-field
                            v-model="search"
                            append-icon="mdi-magnify"
                            label="Search"
                            single-line
                            hide-details
                            class="pa-5"
                        ></v-text-field>
                        <v-data-table
                            v-model="selectedDataObjects"
                            :headers="headers"
                            :items="allDataObjectsForSubject"
                            :search="search"
                            show-select
                        >
                            <!-- eslint-disable-next-line -->
                            <template v-slot:item.file="{ item }">
                                <span>{{ shortFileName(item.file) }}</span>
                            </template>
                        </v-data-table>
                    </div>
                </v-list-item>
            </v-navigation-drawer>

            <div class="pa-5 render-area" :style="mini ?'margin-left: 80px' :'margin-left:520px'">
                <span v-if="selectedDataObjects.length == 0">Select any number of data objects</span>
            </div>
        </div>
    </div>
</template>

<style scoped>
.context-card {
    display: flex;
    column-gap: 40px;
    padding: 10px 20px;
    width: 100%;
    height: 80px;
}
.content-area {
    position: relative;
    min-height: calc(100vh - 161px);
}
.render-area {
    display: flex;
    justify-content: space-around;
}
</style>
