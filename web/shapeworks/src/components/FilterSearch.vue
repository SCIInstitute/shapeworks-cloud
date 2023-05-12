<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api'
import router from '@/router';
import { getDatasets } from '@/api/rest';
import { loadingState, allDatasets, allProjectsForDataset, selectedDataset, selectedProject, loadProjectsForDataset } from '@/store';
import { getProjectsForDataset } from '@/api/rest';


export default defineComponent({
    setup() {
      const searchText = ref(router.currentRoute.params.searchText)

      async function navigateToResults() {
        // use store functions
        loadingState.value = true;
        
        if (selectedDataset.value) {
            // allProjectsForDataset.value = (await getProjectsForDataset(searchText.value, selectedDataset.value.id)).sort((a, b) => {
            //     if(a.created < b.created) return 1;
            //     if(a.created > b.created) return -1;
            //     return 0;
            // });
            router.replace(`dataset/${selectedDataset.value.id}/search/${searchText.value}`)
            loadProjectsForDataset(selectedDataset.value.id);
        } else {
            router.replace('/search/'+searchText.value)
            allDatasets.value = (await getDatasets(searchText.value)).sort((a, b) => {
                if(a.created < b.created) return 1;
                if(a.created > b.created) return -1;
                return 0;
            });
        }
        loadingState.value = false;
      }

      router.beforeEach(async (to, from, next) => {
        if (!to.params.searchText) searchText.value = ''
        next()
      })

      return {
        searchText,
        selectedDataset,
        selectedProject,
        navigateToResults
      }
    }
})
</script>

<template>
    <v-chip>
        <v-text-field
            autofocus
            rounded
            hide-details
            v-model="searchText"
            @input="navigateToResults"
        >
            <template v-slot:prepend-inner>
            <v-icon>
                mdi-magnify
            </v-icon>
            </template>
            <template v-slot:append>
                <v-tooltip bottom>
                    <template v-slot:activator="{ on, attrs }">
                        <span v-bind="attrs" v-on="on">
                            <v-icon>
                                mdi-information-outline
                            </v-icon>
                        </span>
                    </template>
                    <span>Search ShapeWorks datasets by name, description, and keywords</span>
                </v-tooltip>
            </template>
        </v-text-field>
    </v-chip>
</template>
