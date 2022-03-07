<template>
  <div>Groom</div>
</template>

<script lang="ts">
import { loadDatasetAndSubject } from "@/store";
import { defineComponent, onMounted } from "@vue/composition-api";

export default defineComponent({
  props: {
      dataset: {
          type: Number,
          required: true,
      },
      subject: {
          type: Number,
          required: true,
      },
  },
  setup(props) {
    onMounted(async () => {
      await loadDatasetAndSubject(props.dataset, props.subject);
    });
  }
});
</script>
