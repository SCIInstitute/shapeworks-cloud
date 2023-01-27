<script lang="ts">
import { getTaskProgress, deleteTaskProgress } from '@/api/rest';
import { defineComponent, computed, ref, watch } from '@vue/composition-api'
import { currentTasks, pollJobResults } from '../store';


export default defineComponent({
    props: {
        task: {
            type: String,
            required: true,
        }
    },
    setup(props, context) {
        const watchTaskInterval = ref();
        const taskPercentComplete = ref<number>(0)
        const taskErrorMessage = ref<string>();

        const taskId = computed(
            () => currentTasks.value[`${props.task}_task`]
        )

        async function completeTask(){
            if(taskId.value && watchTaskInterval.value){
                const pollMessage = await pollJobResults(props.task)
                clearInterval(watchTaskInterval.value)
                watchTaskInterval.value = undefined
                await deleteTaskProgress(taskId.value)
                context.emit("complete", taskErrorMessage.value || pollMessage)
                currentTasks.value[`${props.task}_task`] = undefined
            }
        }

        async function fetchTask() {
            if(taskId.value && watchTaskInterval.value) {
                const progress = await getTaskProgress(taskId.value)
                if (progress.percent_complete !== undefined) {
                    taskPercentComplete.value = progress.percent_complete
                    if (progress.error.length > 0) {
                        taskErrorMessage.value = progress.error
                        taskPercentComplete.value = -1
                        completeTask()
                    }
                    if (progress.percent_complete === 100) {
                        completeTask()
                    }

                } else {
                    taskErrorMessage.value = "Failed to get task progress"
                }

            }
        }

        watch(taskId, () => watchTaskInterval.value = setInterval(fetchTask, 1000))

        return {
            taskId,
            taskPercentComplete,
            watchTaskInterval,
        }
    }
})
</script>

<template>
  <div v-if="taskId && watchTaskInterval">
    <v-progress-linear :value="taskPercentComplete" v-if="taskPercentComplete > -1"/>
  <br />
  </div>
</template>
