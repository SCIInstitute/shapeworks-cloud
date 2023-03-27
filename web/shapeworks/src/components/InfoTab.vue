<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { selectedDataset, selectedProject } from '../store';

export default defineComponent({
    setup() {
        return {
            selectedDataset,
            selectedProject,
        }
    }
})
</script>

<template>
    <div class="pa-3">
        View / edit project information
        <v-expansion-panels :value="0">
            <v-expansion-panel>
                <v-expansion-panel-header>
                    Landmarks
                </v-expansion-panel-header>
                <v-expansion-panel-content>

                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
    </div>
</template>
