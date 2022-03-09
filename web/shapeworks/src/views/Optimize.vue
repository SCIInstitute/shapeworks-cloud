<template>
  <div>Optimize</div>
</template>

<script lang="ts">
import { loadDataset } from "@/store";
import { defineComponent, onMounted } from "@vue/composition-api";

export default defineComponent({
  props: {
      dataset: {
          type: Number,
          required: true,
      },
  },
  setup(props) {
    onMounted(async () => {
      await loadDataset(props.dataset);
    });
  }
});
</script>
