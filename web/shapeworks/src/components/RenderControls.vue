<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import {
    particleSize,
    layers,
    layersShown,
} from '../store';


export default defineComponent({
    setup() {
        return {
            particleSize,
            layersShown,
            layers,
        }
    }
})
</script>

<template>
    <div class="render-control-bar">
        <v-select
            v-model="layersShown"
            :items="layers"
            label="Layers shown"
            style="width: 500px"
            multiple
            small-chips
            item-text="name"
        >
            <template #selection="{ item }">
                <v-chip
                    close
                    @click:close="layersShown.splice(index, 1)"
                    :color="item.color"
                    :text-color="item.color === 'white' ? 'black' : 'white'"
                >
                    {{ item.name }}
                </v-chip>
            </template>
        </v-select>
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
    height: 70px;
    justify-content: space-between;
}
.render-control-bar > * {
    flex-grow: 0;
}
</style>
