<script lang="ts">
import {
    analysis, analysisFileShown,
    currentAnalysisFileParticles, meanAnalysisFileParticles,
    currentTasks,
    selectedProject,
    analysisExpandedTab,
calculateComparisons,
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
import imageReader from '../reader/image';
import pointsReader from '../reader/points';
import generateMapper from '@/reader/mapper';
import { cacheComparison } from '@/store';
import { cachedParticleComparisonColors } from '@/store';

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
        const animate = ref<boolean>(false);
        const currentlyCaching = ref<boolean>(false);
        const currGroup = ref<AnalysisGroup>();

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

        // determine if the currently selected group pairing is inverted
        // returns true if they are inverted, false if not
        const pairingIsInverted = (g: any) => {
            return (g.group1 === currPairing.value.right && g.group2 === currPairing.value.left)
        }
        
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
                    {key: 'Lambda', value: currPCA.value?.lambda_value || 0},
                    {key: 'Eigenvalue', value: currMode.value?.eigen_value},
                    {key: 'Explained Variance', value: currMode.value?.explained_variance, class: 'percentage'},
                    {key: 'Cumulative Explained Variance', value: currMode.value?.cumulative_explained_variance, class:'percentage'},
                ],
            }
        })


        const updateCurrGroup = () => {
            currGroup.value = analysis.value?.groups.find((g) => {
                if (g.name === groupSet.value) {
                    if (!pairingIsInverted(g))  { // in-order group pairings
                        if (g.ratio === groupRatio.value) {
                            return true;
                        }
                    } else if (pairingIsInverted(g)) { // inverted group pairings
                        if (g.ratio === parseFloat((1 - groupRatio.value).toFixed(1))) { // floating point precision errors (https://en.wikipedia.org/wiki/Floating-point_arithmetic#Accuracy_problems)
                            return true;
                        }
                    }
                }
            })
        }

        async function cacheAllComparisons() {
            const allInPairing = analysis.value?.groups.filter((g) => {
                if (g.name === groupSet.value) { // if groupSet is same
                    if ((g.group1 === currPairing.value.left || g.group1 === currPairing.value.right) && (g.group2 === currPairing.value.left || g.group2 === currPairing.value.right))
                        return true;
                }
            })

            if (allInPairing !== undefined) {
                const cachePrep = await Promise.all(allInPairing?.map(async (g) => {
                    const particleComparisonKey = `${g.particles}_${meanAnalysisFileParticles.value}`;

                    if (!cachedParticleComparisonColors.value[particleComparisonKey]) { // if the comparison is NOT already cached
                        const compareToPoints = await pointsReader(meanAnalysisFileParticles.value);
                        const currentPoints = await pointsReader(g.particles);

                        const currentMesh = await imageReader(g.file, "current_mesh.vtk");

                        return {
                            "compareTo": {
                                points: compareToPoints.getPoints().getData(),
                                particleUrl: meanAnalysisFileParticles.value,
                            },
                            "current":  {
                                points: currentPoints.getPoints().getData(),
                                mapper: generateMapper(currentMesh),
                                particleUrl: g.particles,
                            }, 
                        }
                    }
                }))

                cachePrep.forEach((g) => {
                    if (g !== undefined) {
                        const { current, compareTo } = g;
                        const comparisons = calculateComparisons(current.mapper, current.points, compareTo.points)
                        cacheComparison(comparisons.colorValues, comparisons.vectorValues, `${current.particleUrl}_${compareTo.particleUrl}`);
                    }
                })
            }
        }

        let step = 0.1;
        const animateSlider = () => {
            if (openTab.value === 1) { // Group tab animate
                if (groupRatio.value === 0) step = 0.1;
                if (groupRatio.value === 1) step = -0.1;
                groupRatio.value = parseFloat((groupRatio.value + step).toFixed(1));
            }
        }

        let intervalId: number;
        async function triggerAnimate() {
            if (groupSet.value === undefined) return;

            if (animate.value) {
                currentlyCaching.value = true;
                await cacheAllComparisons();
                currentlyCaching.value = false;
                intervalId = setInterval(animateSlider, 500);
            }
            if (animate.value === false && intervalId) {
                clearInterval(intervalId);
            }
        }

        const setDefaultPairing = () => {
            // default left and right group selections: first and second item in groupSet pairings list
            if (groupSet.value !== undefined) {
                currPairing.value.left = groupPairings.value[groupSet.value][0];
                currPairing.value.right = groupPairings.value[groupSet.value][1];
                prevPairing.value = {left: currPairing.value.left, right: currPairing.value.right};
            }
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
            updateCurrGroup();

            if (props.currentTab === 'analyze' && analysis.value && currGroup.value){
                fileShown = currGroup.value.file;
                particles = currGroup.value.particles;
            }
            currentAnalysisFileParticles.value = particles;
            if (groupDiff.value) {
                meanAnalysisFileParticles.value = analysis.value?.groups.find((g) => {
                    if (g.name === groupSet.value) {
                      if (!pairingIsInverted(g)) {
                        if (g.ratio === 1.0) return true;
                      } else if (pairingIsInverted(g)) {
                        if (g.ratio === 0.0) return true;
                      }
                    }
                })?.particles // account for inverted-pairings
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
        watch(groupSet, () => {
            setDefaultPairing(); 
            updateGroupFileShown();
        })
        watch(currPairing.value, updateGroupSelections)
        watch(groupRatio, updateGroupFileShown)
        watch(groupDiff, updateGroupFileShown)
        watch(animate, triggerAnimate)
        watch(openTab, () => {
            analysisExpandedTab.value = openTab.value;
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
            animate,
            openTab,
            currentlyCaching
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
            <v-expansion-panel :disabled="allGroupSets === undefined || allGroupSets.length === 0" id="groups-panel">
                <v-expansion-panel-header>
                    Group Difference
                </v-expansion-panel-header>
                <v-expansion-panel-content>
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
                                :disabled="currGroup === undefined"
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
                            :disabled="currGroup === undefined"
                            class="mt-0 mb-8 pt-0"
                            v-model="animate"
                            label="Animate"
                            hide-details
                        ></v-checkbox>
                    </v-row>
                    <v-card align="center" justify="center" class="ma-auto mb-3" :disabled="currGroup === undefined">
                        <v-btn class="ms-4" color="grey darken-3" @click="() => groupRatio = 0.0">Left Mean</v-btn>
                        <v-btn-toggle class="ms-4" color="white"><v-btn color="grey darken-4" :disabled="animate || currentlyCaching" @click="() => groupDiff = !groupDiff">Diff --></v-btn></v-btn-toggle>
                        <v-btn class="ms-4" color="grey darken-3" @click="() => groupRatio = 1.0">Right Mean</v-btn>
                    </v-card>
                    <div class="loading-dialog"><v-dialog v-model="currentlyCaching" width="10%">Calculating...  <v-progress-circular indeterminate align-center></v-progress-circular></v-dialog></div>
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

.v-dialog {
    overflow: hidden;
}

.loading-dialog {
    display: flex;
    justify-content: center;
}

.v-btn-toggle:not(.v-btn-toggle--dense) .v-btn.v-btn.v-size--default {
    height: 36px !important;
}

</style>
