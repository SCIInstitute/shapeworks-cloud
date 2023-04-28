<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api'
import router from '@/router';
import { getDatasets } from '@/api/rest';
import { loadingState, allDatasets } from '@/store';


export default defineComponent({
    setup() {
      const searchText = ref(router.currentRoute.params.searchText)

      async function navigateToResults() {
        router.replace('/search/'+searchText.value)
        loadingState.value = true;
        allDatasets.value = (await getDatasets(searchText.value)).sort((a, b) => {
            if(a.created < b.created) return 1;
            if(a.created > b.created) return -1;
            return 0;
        });
        loadingState.value = false;
      }

      return {
        searchText,
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
                    <span>Search ShapeWorks datasets by title, description, and keywords</span>
                </v-tooltip>
            </template>
        </v-text-field>
    </v-chip>
</template>
