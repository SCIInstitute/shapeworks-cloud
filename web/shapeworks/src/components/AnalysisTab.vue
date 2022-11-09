<script lang="ts">
import { refreshProject } from '@/api/rest'
import router from '@/router';
import { selectedProject } from '@/store'
import { defineComponent, ref } from '@vue/composition-api'

export default defineComponent({
    setup() {
        const analysis = ref(selectedProject.value?.last_cached_analysis)

        async function refresh() {
            if(!selectedProject.value) {
                router.push({
                    name: 'select',
                });
                return;
            }
            // refresh project last cached analysis
            const refreshedProject = await refreshProject(selectedProject.value.id)
            if (refreshedProject) analysis.value = refreshedProject.last_cached_analysis
            console.log(analysis.value)
        }
        refresh()

        return {
            refresh,
            analysis,
        }
    },
    beforeUpdate() {
        this.refresh()
    }
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
