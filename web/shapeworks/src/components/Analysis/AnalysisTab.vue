<script lang="ts">
import {
    analysis, analysisFileShown,
    currentTasks,
    selectedProject,
    analysisExpandedTab,
} from '@/store'
import { defineComponent, ref, computed, watch, provide } from '@vue/composition-api'
import Charts from './Charts.vue'
import Groups from './Groups.vue'
import PCA from './PCA.vue'

export enum AnalysisTabs {
    PCA = 0,
    Groups,
    Charts
}

export default defineComponent({
    props: {
        currentTab: {
            type: String,
            required: true,
        }
    },
    components: {
        Charts,
        Groups,
        PCA
    },
    setup(props) {
        const openTab = ref(AnalysisTabs.PCA);
        const message = ref<string>();
        const currentlyCaching = ref<boolean>(false);

        const pca = ref();
        const groups = ref();

        // provide mutable ref for use in child components
        provide('currentlyCaching', currentlyCaching);

        const taskData = computed(
            () => {
                if (!selectedProject.value || !currentTasks.value[selectedProject.value.id]) return undefined
                return currentTasks.value[selectedProject.value.id]['analyze_task']
            }
        )

        watch(openTab, () => {
            analysisExpandedTab.value = openTab.value;
            switch(openTab.value) {
                case AnalysisTabs.PCA:
                    groups.value.methods.stopAnimating();
                    pca.value.methods.updateFileShown();
                    break;
                case AnalysisTabs.Groups:
                    pca.value.methods.stopAnimating();
                    if (groups.value.currGroup) {
                        groups.value.methods.updateGroupFileShown();
                    }
                    break;
                case AnalysisTabs.Charts:
                    groups.value.methods.stopAnimating();
                    pca.value.methods.stopAnimating();
                    break;
            }
        })

        return {
            analysis,
            analysisFileShown,
            message,
            taskData,
            openTab,
            currentlyCaching,
            pca,
            groups
        }
    },
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
                    <PCA ref="pca" :currentTab="currentTab" :openTab="openTab"/>
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
                    Charts
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                    <charts :charts="analysis.charts"/>
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
        <div class="loading-dialog"><v-dialog v-model="currentlyCaching" width="10%">Calculating...  <v-progress-circular indeterminate align-center></v-progress-circular></v-dialog></div>
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

.messages-box {
    text-align: center;
    color: #2196f3;
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
