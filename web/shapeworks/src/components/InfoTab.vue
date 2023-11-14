<script lang="ts">
import { onMounted, ref, watch } from 'vue'
import Landmarks from '@/components/Landmarks.vue';
import Constraints from '@/components/Constraints.vue';
import { layers, layersShown } from '@/store';


export default {
    components: {
        Landmarks,
        Constraints
    },
    setup() {
        const openPanel = ref(0)

        function updateLayersShown() {
            layersShown.value = layers.value.filter((l) => {
                if (l.name === 'Landmarks') {
                    return openPanel.value === 0
                } else if (l.name === 'Constraints') {
                    return openPanel.value === 1
                }
                return layersShown.value.includes(l.name)
            }).map((l) => l.name)
        }

        watch(openPanel, updateLayersShown)
        onMounted(updateLayersShown)

        return {
            openPanel,
        }
    }
}
</script>

<template>
  <v-expansion-panels v-model="openPanel">
    <landmarks />
    <constraints />
  </v-expansion-panels>
</template>
