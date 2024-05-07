<script lang="ts">
import {
    analysis,
    analysisExpandedTab,
    jobAlreadyDone,
} from '@/store'
import { ref, watch, provide } from 'vue'
import Charts from './Charts.vue'
import Groups from './Groups.vue'
import Particles from './Particles.vue'
import PCA from './PCA.vue'
import { AnalysisTabs } from './util';
import TaskInfo from '../TaskInfo.vue'
import { AnalysisParams } from '@/types'

export default {
    props: {
        currentTab: {
            type: String,
            required: true,
        }
    },
    components: {
        Charts,
        Groups,
        Particles,
        PCA,
        TaskInfo,
    },
    setup() {
        const formDefaults: AnalysisParams = {range: 2, steps: 11}
        const openTab = ref(AnalysisTabs.PCA);
        const formData = ref<AnalysisParams>({...formDefaults});
        const currentlyCaching = ref<boolean>(false);

        const pca = ref();
        const groups = ref();

        // provide mutable ref for use in child components
        provide('currentlyCaching', currentlyCaching);

        watch(openTab, () => {
            analysisExpandedTab.value = openTab.value;
            switch(openTab.value) {
                case AnalysisTabs.PCA:
                    if (groups.value) {
                        groups.value.methods.stopAnimating();
                    }
                    pca.value.methods.updateFileShown();
                    break;
                case AnalysisTabs.Groups:
                    pca.value.methods.stopAnimating();
                    if (groups.value) {
                        if (groups.value.currGroup) {
                            groups.value.methods.updateGroupFileShown();
                        }
                    }
                    break;
                case AnalysisTabs.Charts:
                    if (groups.value) {
                        groups.value.methods.stopAnimating();
                    }
                    pca.value.methods.stopAnimating();
                    break;
                case AnalysisTabs.Particles:
                    if (groups.value) {
                        groups.value.methods.stopAnimating();
                    }
                    pca.value.methods.stopAnimating();
                    break;
            }
        })

        function resetForm() {
            formData.value = formDefaults
        }

        return {
            analysis,
            formData,
            openTab,
            currentlyCaching,
            pca,
            groups,
            resetForm,
            jobAlreadyDone
        }
    },
}
</script>

<template>
    <div v-if="jobAlreadyDone('optimize')">
        <v-expansion-panels :value="analysis ? 1 : 0">
            <v-expansion-panel>
                <v-expansion-panel-header>Controls</v-expansion-panel-header>
                <v-expansion-panel-content>
                    <task-info
                        taskName="analyze"
                        :formData="formData"
                        @resetForm="resetForm"
                        :disabled="!analysis"
                    />
                    <v-text-field
                        v-model.number="formData.range"
                        type="number"
                        step="1.0"
                        max="10.0"
                        min="1.0"
                        label="Std. Dev. Range"
                        hide-details
                        :disabled="!analysis"
                    />
                    <v-text-field
                        v-model.number="formData.steps"
                        type="number"
                        step="1.0"
                        min="1.0"
                        max="100.0"
                        label="Number of steps"
                        hide-details
                        :disabled="!analysis"
                    />
                </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel v-if="analysis">
                <v-expansion-panel-header>Results</v-expansion-panel-header>
                <v-expansion-panel-content>
                    <div class="pa-3">
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
                                    <PCA ref="pca" :currentTab="currentTab" :openTab="openTab"/>
                                    <charts :charts="analysis.charts"/>
                                </v-expansion-panel-content>
                            </v-expansion-panel>
                            <v-expansion-panel :disabled="analysis.groups.length <= 0" id="groups-panel">
                                <v-expansion-panel-header>
                                    Group Difference
                                </v-expansion-panel-header>
                                <v-expansion-panel-content>
                                    <groups ref="groups" :currentTab="currentTab" :openTab="openTab"/>
                                </v-expansion-panel-content>
                            </v-expansion-panel>
                            <v-expansion-panel>
                                <v-expansion-panel-header>
                                    Particles
                                </v-expansion-panel-header>
                                <v-expansion-panel-content>
                                    <particles />
                                </v-expansion-panel-content>
                            </v-expansion-panel>
                        </v-expansion-panels>
                        <div class="loading-dialog"><v-dialog v-model="currentlyCaching" width="10%">Calculating...  <v-progress-circular indeterminate align-center></v-progress-circular></v-dialog></div>
                    </div>
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
    </div>
    <div v-else class="pa-3" style="text-align: center;">Perform optimization before analyzing.</div>
</template>

<style>
.percentage>.text-end::after {
    content: ' %'
}

.v-dialog {
    overflow: hidden;
    background: none;
    box-shadow: none;
}

.loading-dialog {
    display: flex;
    justify-content: center;
}

.v-btn-toggle:not(.v-btn-toggle--dense) .v-btn.v-btn.v-size--default {
    height: 36px !important;
}

</style>
