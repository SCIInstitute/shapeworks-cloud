<script lang="ts">
import {
    analysis, analysisFileShown,
    currentAnalysisFileParticles, meanAnalysisFileParticles,
    currentTasks,
    selectedProject,
} from '@/store'
import { defineComponent, ref, computed, watch } from '@vue/composition-api'
import { lineChartOptions } from '@/charts'
import { AnalysisChart, AnalysisGroup } from '@/types'

import { use } from 'echarts/core';
import { SVGRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  ToolboxComponent,
  DataZoomComponent
} from 'echarts/components';
import VChart from 'vue-echarts';

// registers required echarts components
use([SVGRenderer,LineChart,TitleComponent,TooltipComponent,GridComponent,ToolboxComponent,DataZoomComponent]);

export default defineComponent({
    props: {
        currentTab: {
            type: String,
            required: true,
        }
    },
    setup(props) {
        const openTab = ref(0);
        const mode = ref(1);
        const stdDev = ref(0);
        const groupRatio = ref(0.5);
        const groupDiff = ref(false);
        const groupSet = ref<string>();
        const currPairing = ref<{left: string, right: string}>({left:"", right:""});
        const prevPairing = ref<{left: string, right: string}>({left:"", right:""}); // stores the previously selected pairing
        const message = ref<string>();

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

        const currGroup = computed(() => {
            return analysis.value?.groups.find((g) => {
                if (g.name === groupSet.value) {
                    if (g.group1 === currPairing.value.left && g.group2 === currPairing.value.right)  { // in-order group pairings
                        if (g.ratio === groupRatio.value) {
                            return true;
                        }
                    } else if (g.group1 === currPairing.value.right && g.group2 === currPairing.value.left) { // inverted group pairings
                        if (g.ratio === parseFloat((1 - groupRatio.value).toFixed(1))) { // floating point precision errors (https://en.wikipedia.org/wiki/Floating-point_arithmetic#Accuracy_problems)
                            return true;
                        }
                    }
                }
            })
        })

        const allGroupSets = computed(() => { 
            return analysis.value?.groups.map((g) => g.name); 
        })

        // get all possible unique group pairings
        const groupPairings = computed(() => {
            const g: { [name: string]: string[] } = {};
            analysis.value?.groups.map((group: AnalysisGroup) => {
                if (g[group.name] === undefined) g[group.name] = [];
                if (!g[group.name].includes(group.group1)) g[group.name].push(group.group1);
                if (!g[group.name].includes(group.group2)) g[group.name].push(group.group2);
            })
            return g;
        });

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
                    {key: 'Lambda', value: currPCA.value?.lambda_value || 0},
                    {key: 'Eigenvalue', value: currMode.value?.eigen_value},
                    {key: 'Explained Variance', value: currMode.value?.explained_variance, class: 'percentage'},
                    {key: 'Cumulative Explained Variance', value: currMode.value?.cumulative_explained_variance, class:'percentage'},
                ],
            }
        })

        const setDefaultPairing = () => {
            // default left and right group selections: first and second item in groupSet pairings list
            if (groupSet.value !== undefined) {
                currPairing.value.left = groupPairings.value[groupSet.value][0];
                currPairing.value.right = groupPairings.value[groupSet.value][1];
                prevPairing.value = {left: currPairing.value.left, right: currPairing.value.right};
            }

            updateGroupFileShown();
        }

        // triggered on group pairing select change
        const updateGroupSelections = () => {
            // if the new left and right groups are the same, flip the two values according to the previous selections
            if (currPairing.value.left === currPairing.value.right && groupSet.value !== undefined) {
                // set new non-changed side to opposite side in old pairing
                if (currPairing.value.left === prevPairing.value.left) {
                    currPairing.value.left = prevPairing.value.right;
                }
                if (currPairing.value.right === prevPairing.value.right) {
                    currPairing.value.right = prevPairing.value.left;
                }
            }   
            
            prevPairing.value.left = currPairing.value.left;
            prevPairing.value.right = currPairing.value.right;

            updateGroupFileShown();
        }

        const updateGroupFileShown = () => {
            let fileShown = undefined;
            let particles = undefined;

            if (props.currentTab === 'analyze' && analysis.value && currGroup.value){
                fileShown = currGroup.value.file;
                particles = currGroup.value.particles;
            }
            currentAnalysisFileParticles.value = particles;
            if (groupDiff.value) {
                meanAnalysisFileParticles.value = analysis.value?.groups.find((g) => g.name === groupSet.value && g.ratio === 1.0)?.particles
            } else {
                meanAnalysisFileParticles.value = analysis.value?.mean_particles;
            }

            analysisFileShown.value = fileShown;
        }

        function updateFileShown() {
            let fileShown = undefined
            let particles = undefined
            if (props.currentTab === 'analyze' && analysis.value){
                if (stdDev.value === 0) {
                    fileShown = analysis.value.mean_shape
                    particles = analysis.value.mean_particles;
                } else {
                    fileShown = currPCA.value?.file
                    particles = currPCA.value?.particles
                }
            }
            currentAnalysisFileParticles.value = particles;
            meanAnalysisFileParticles.value =  analysis.value?.mean_particles;
            analysisFileShown.value = fileShown;

        }
        updateFileShown()

        watch(mode, updateFileShown)
        watch(stdDev, updateFileShown)
        watch(props, updateFileShown)
        watch(analysis, updateFileShown)
        watch(groupSet, setDefaultPairing)
        watch(currPairing.value, updateGroupSelections)
        watch(groupRatio, updateGroupFileShown)
        watch(groupDiff, updateGroupFileShown)
        watch(openTab, () => {
            switch(openTab.value) {
                case 0: // PCA
                    updateFileShown();
                    break;
                case 1: // GROUP
                    updateGroupFileShown();
                    break;
                case 2: // CHARTS
                    break;
            }
        })

        const generateChart = (options: AnalysisChart) => {
            return lineChartOptions(options);
        }

        const taskData = computed(
            () => {
                if (!selectedProject.value || !currentTasks.value[selectedProject.value.id]) return undefined
                return currentTasks.value[selectedProject.value.id]['analyze_task']
            }
        )

        return {
            analysis,
            openTab,
            modeOptions,
            mode,
            stdDev,
            stdDevRange,
            pcaInfo,
            analysisFileShown,
            generateChart,
            message,
            taskData,
            groupRatio,
            groupDiff,
            groupSet,
            allGroupSets,
            groupPairings,
            currGroup,
            currPairing,
        }
    },
    components: {
        VChart,
    }
})
</script>

<template>
    <div v-if="taskData" class="messages-box pa-3">
        Running analysis after optimization step...
        <div v-if="taskData.error">{{ taskData.error }}</div>
        <v-progress-linear v-else :value="taskData.percent_complete"/>
        <br />
    </div>
    <div class="pa-3" v-else-if="analysis">
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


         <v-expansion-panels v-model="openTab">
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
                        tick-size="4"
                        thumb-label
                        track-color="#aaa"
                        track-fill-color="#aaa"
                        label="Std. Devs. from Mean"
                    />
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
            <v-expansion-panel :disabled="allGroupSets === undefined || allGroupSets.length === 0">
                <v-expansion-panel-header>
                    Group Difference
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <!-- set group options, SET OPTIONS WHEN BACKEND INCLUDES THEM. MODE IS PLACEHOLDER-->
                    <v-select
                        label="Group Set"
                        v-model="groupSet"
                        :items="allGroupSets"
                        item-text="set"
                        item-value="set"
                    />
                    <v-divider></v-divider>
                    <v-row 
                        align="center" 
                        justify="center"
                    >
                        <v-col>
                            <v-select
                                v-model="currPairing.left"
                                :items="(currGroup && groupSet) ? groupPairings[groupSet] : ['']"
                                item-text="group1"
                                item-value="group1"
                            />
                        </v-col>
                        <v-col>
                            <v-slider
                                v-model="groupRatio"
                                min="0.0"
                                max="1.0"
                                step="0.1"
                                default="0.5"
                                show-ticks="always"
                                hide-details
                            ></v-slider>
                        </v-col>
                        <v-col>
                            <v-select
                                v-model="currPairing.right"
                                :items="(currGroup && groupSet) ? groupPairings[groupSet] : ['']"
                                item-text="group2"
                                item-value="group2"
                            />
                        </v-col>
                    </v-row>
                    <v-row justify="center">
                        <v-checkbox
                            class="mt-0 mb-8 pt-0"
                            value
                            label="Animate"
                            hide-details
                        ></v-checkbox>
                    </v-row>
                    <v-card align="center" justify="center" class="ma-auto" :disabled="currGroup === undefined">
                        <v-btn class="ms-4" color="grey darken-3" @click="() => groupRatio = 0.0">Mean</v-btn>
                        <v-btn class="ms-4" color="grey darken-3" @click="() => groupDiff = !groupDiff">Diff --></v-btn>
                        <v-btn class="ms-4" color="grey darken-3" @click="() => groupRatio = 1.0">Mean</v-btn>
                    </v-card>
                </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel>
                <v-expansion-panel-header>
                    Charts
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-chart class="chart" v-for="chart in analysis.charts" :key="chart.title" :option="generateChart(chart)" />
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
    </div>
    <div v-else class="messages-box pa-3">
        {{ message ||
            "No analysis generated yet; run the optimization step to generate an analysis."
        }}
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

.dataview {
    height: 100%;
    width: 100%;
}

.datatable {
    color: #000000;
    width: 100%;
}

.datatable tbody tr:nth-child(even) {
    background-color: #e5e4e2;
}

.datatable-row td {
    padding-right: 30px;
}

.dataview-button {
    background: #2196f3;
    border-radius: 3px;
    cursor: pointer;
    padding: 2px 5px;
    font-size: 12px;
    z-index: 1;
}

.dataview-button:hover {
    background: #318dd8;
}

.copy-button {
    position: absolute;
    bottom: 5px;
    right: 70px;
}

.download-button {
    position: absolute;
    bottom: 5px;
    right: 185px;
}

.dataview-text {
    display: block;
    height: 100%;
    width: 100%;
    font-family: monospace;
    font-size: 14px;
    line-height: 1.6rem;
    resize: none;
    border: 1px solid #333333;
}

.messages-box {
    text-align: center;
    color: #2196f3;
}

</style>
