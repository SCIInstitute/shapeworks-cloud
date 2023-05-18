<script lang="ts">
import { defineComponent, onBeforeUpdate, ref, watch } from '@vue/composition-api'
import router from '@/router';
import { selectedDataset, selectedProject } from '@/store';

export default defineComponent({
    setup() {
      const searchText = ref(router.currentRoute.params.searchText)

      async function navigateToResults() {
        // use store functions
        let targetUrl = "/"
        if (selectedDataset.value) {
            targetUrl = `/dataset/${selectedDataset.value.id}/`
        }

        if (searchText.value) {
            targetUrl = targetUrl + `search/${searchText.value}`
        }

        router.push(targetUrl);
      }

      router.beforeEach(async (to, from, next) => {
        if (!to.params.searchText) searchText.value = ''
        searchText.value = to.params.searchText;
        next()
      })

      return {
        searchText,
        selectedDataset,
        selectedProject,
        navigateToResults
      }
    },
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
                    <span>Search ShapeWorks {{(selectedDataset) ? "projects" : "datasets"}} by name, description, and keywords</span>
                </v-tooltip>
            </template>
        </v-text-field>
    </v-chip>
</template>
