<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import {
    particleSize,
    layersShown,
} from '../store';


export default defineComponent({
    setup() {
        const layersOptions = [
            "Original", "Groomed", "Reconstructed", "Particles"
        ]

        return {
            particleSize,
            layersShown,
            layersOptions,
        }
    }
})
</script>

<template>
    <div class="render-control-bar">
        <v-combobox
            v-model="layersShown"
            :items="layersOptions"
            label="Layers shown"
            style="width: 250px"
            multiple
            small-chips
        />
        <v-text-field
            v-model.number="particleSize"
            v-if="layersShown.includes('Particles')"
            label="Particle Size"
            type="number"
            style="width: 80px"
            step="0.5"
            min="0.5"
            max="10"
            hide-details
        />
    </div>
</template>

<style scoped>
.render-control-bar {
    display: flex;
    width: 100%;
    justify-content: space-between;
}
.render-control-bar > * {
    flex-grow: 0;
}
</style>
