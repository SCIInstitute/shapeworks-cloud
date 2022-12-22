<script lang="ts">
import { refreshProject } from '@/api/rest'
import router from '@/router';
import { analysisFileShown, selectedProject } from '@/store'
import { defineComponent, ref, computed, watch } from '@vue/composition-api'
import { lineChartOptions, lineChartProps } from '@/charts'

import { use } from 'echarts/core';
import { SVGRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  ToolboxComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';

// registers required echarts components
use([SVGRenderer,LineChart,TitleComponent,TooltipComponent,GridComponent,ToolboxComponent]);

export default defineComponent({
    props: {
        currentTab: {
            type: String,
            required: true,
        }
    },
    setup(props) {
        const analysis = ref(selectedProject.value?.last_cached_analysis)
        const mode = ref(1);
        const stdDev = ref(0);

        const modeOptions = computed(() => {
            return analysis.value?.modes.sort((a, b) => a.mode - b.mode)
        })

        const currMode = computed(() => {
            return analysis.value?.modes.find((m) => m.mode == mode.value)
        })

        const currPCA = computed(() => {
            return currMode.value?.pca_values.find(
                p => p.pca_value.toPrecision(2) === stdDev.value.toPrecision(2)
            )
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

        const pcaInfo = computed(() => {
            return {
                headers: [
                    {text: 'key', value: 'key'},
                    {text: 'value', value: 'value', align: 'end'}
                ],
                items: [
                    {key: 'Lambda', value: currPCA.value?.lambda_value},
                    {key: 'Eigenvalue', value: currMode.value?.eigen_value},
                    {key: 'Explained Variance', value: currMode.value?.explained_variance, class: 'percentage'},
                    {key: 'Cumulative Explained Variance', value: currMode.value?.cumulative_explained_variance, class:'percentage'},
                ],
            }
        })

        function updateFileShown() {
            let fileShown = undefined
            if (props.currentTab === 'analyze' && analysis.value){
                if (stdDev.value === 0) {
                    fileShown = analysis.value.mean_shape
                } else {
                    fileShown = currPCA.value?.file
                }
            }
            analysisFileShown.value = fileShown;
        }
        updateFileShown()

        watch(mode, updateFileShown)
        watch(stdDev, updateFileShown)
        watch(props, updateFileShown)

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
        }

        function generateChart(options: lineChartProps) {
            return lineChartOptions(options);
        }

        return {
            refresh,
            analysis,
            modeOptions,
            mode,
            stdDev,
            stdDevRange,
            pcaInfo,
            analysisFileShown,
            generateChart
        }
    },
    components: {
        VChart
    },
    mounted() {
        this.refresh()
    }
})
</script>

<template>
    <div class="pa-3" v-if="analysis">
        Review shape analysis
        <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
                <v-icon
                    v-bind="attrs"
                    v-on="on"
                >
                mdi-information
                </v-icon>
            </template>
            <span>
               <v-subheader>Last analysis run at {{ analysis.modified }}</v-subheader>
            </span>
        </v-tooltip>


         <v-expansion-panels :value="0">
            <v-expansion-panel>
                <v-expansion-panel-header>
                    View PCA
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-select
                        label="Select mode"
                        v-model="mode"
                        :items="modeOptions"
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
                    <br/>
                    <v-data-table
                        :headers="pcaInfo.headers"
                        :items="pcaInfo.items"
                        item-class="class"
                        hide-default-header
                        hide-default-footer
                    />
                </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel>
                <v-expansion-panel-header>
                    Charts
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-chart class="chart" v-for="chart in (analysis.charts as any)" :key="chart.title" :option="generateChart(chart)" />
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
    </div>
    <div class="pa-3" v-else>
        No analysis generated yet; run the optimization step to generate an analysis.
    </div>
</template>

<style>
.percentage>.text-end::after {
    content: ' %'
}

.chart {
    height: 400px;
    width: 400px;
}
</style>
