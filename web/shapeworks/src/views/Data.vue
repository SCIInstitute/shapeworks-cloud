<script lang="ts">
import { getDataObjectsForSubject } from '@/api/rest';
import { defineComponent, onMounted } from '@vue/composition-api';
import { selectedDataset, selectedSubject } from '../store';


export default defineComponent({
    setup() {
        onMounted(async () => {
            if (!selectedSubject.value) return;
            await getDataObjectsForSubject(selectedSubject.value.id)
        })

        return {
            selectedDataset,
            selectedSubject,
        }
    }
})
</script>


<template>
    <div>
        <div class="context-card">
            <div>
                <div class="text-overline">
                    DATASET ({{ selectedDataset.created.split('T')[0] }})
                </div>
                <v-list-item-title class="text-h6 mb-1">
                    {{ selectedDataset.name }}
                </v-list-item-title>
            </div>
            <div>
                <div class="text-overline">
                    SUBJECT ({{ selectedSubject.created.split('T')[0] }})
                </div>
                <v-list-item-title class="text-h6 mb-1">
                    {{ selectedSubject.name }}
                </v-list-item-title>
            </div>
        </div>
        <v-divider />

    </div>
</template>

<style scoped>
.context-card {
    display: flex;
    column-gap: 40px;
    padding: 10px 20px;
    width: 100%
}
</style>
