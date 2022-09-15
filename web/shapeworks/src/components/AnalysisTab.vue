<script lang="ts">
import { selectedProject } from '@/store'
import { defineComponent } from '@vue/composition-api'

export default defineComponent({
    setup() {
        console.log(selectedProject.value?.last_cached_analysis)
    },
})
</script>

<template>
    <div class="pa-3">
        Analysis content here
         <v-expansion-panels :value="0">
            <v-expansion-panel>
                <v-expansion-panel-header>
                    View PCA
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    slider goes here
                </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel>
                <v-expansion-panel-header>
                    Charts
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    Charts go here
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
    </div>
</template>
