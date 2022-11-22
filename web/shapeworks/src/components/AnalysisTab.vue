<script lang="ts">
import { refreshProject } from '@/api/rest'
import router from '@/router';
import { analysisFileShown, selectedProject } from '@/store'
import { defineComponent, ref, computed, watch } from '@vue/composition-api'

export default defineComponent({
    setup() {
        const analysis = ref(selectedProject.value?.last_cached_analysis)
        const mode = ref(1);
        const stdDev = ref(0);

        const currMode = computed(() => {
            return analysis.value?.modes.find((m) => m.mode == mode.value)

        })

        const stdDevRange = computed(() => {
            if (!analysis.value || !currMode.value) return [0, 0, 0]
            const pcaValues = currMode.value.pca_values.map(p => p.pca_value)
            const min =  Math.min(...pcaValues);
            const max =  Math.max(...pcaValues)
            const step = (max - min) / pcaValues.length
            return [
                min, max, step
            ]
        })

        function updateFileShown() {
            if (analysis.value){
                let fileShown = undefined
                if (stdDev.value === 0) {
                    fileShown = analysis.value.mean_shape
                } else {
                    fileShown = currMode.value?.pca_values.find(
                        p => p.pca_value.toPrecision(2) === stdDev.value.toPrecision(2)
                    )?.file
                }
                analysisFileShown.value = fileShown;
            }
        }
        updateFileShown()

        watch(mode, updateFileShown)
        watch(stdDev, updateFileShown)

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

        return {
            refresh,
            analysis,
            mode,
            stdDev,
            stdDevRange,
            analysisFileShown
        }
    },
    mounted() {
        this.refresh()
    }
})
</script>

<template>
    <div class="pa-3">
        Review shape analysis
         <v-expansion-panels :value="0">
            <v-expansion-panel>
                <v-expansion-panel-header>
                    View PCA
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-select
                        label="Select mode"
                        v-model="mode"
                        :items="analysis.modes"
                        item-text="mode"
                        item-value="mode"
                    />
                    <v-slider
                        v-model="stdDev"
                        :min="stdDevRange[0]"
                        :max="stdDevRange[1]"
                        :step="stdDevRange[2]"
                        ticks="always"
                        tick-size="8"
                    >
                        <template v-slot:prepend>
                            Std. Devs. from Mean
                        </template>
                    </v-slider>
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
