<script lang="ts">
import { computed, ref, watch } from 'vue';
import {
    selectedProject,
    currentTasks,
    jobAlreadyDone,
    fetchJobResults,
    spawnJob,
    abort,
} from '@/store';

export default {
  props: {
    taskName: {
        type: String,
        required: true
    },
    formData: {
        type: Object,
        required: false,
    },
    formDefaults: {
        type: Object,
        required: false,
    },
  },
  setup(props, { emit }) {
    const showSubmissionConfirmation = ref(false);
    const showAbortConfirmation = ref(false);
    const alreadyDone = ref(jobAlreadyDone(props.taskName))

    const taskData = computed(
        () => {
            if(!selectedProject.value?.id ||
            !currentTasks.value[selectedProject.value.id]) return undefined
            return currentTasks.value[selectedProject.value.id][props.taskName]
        }
    )

    watch(taskData, async (value, oldValue) => {
        if (value === undefined && oldValue !== undefined) {
            await fetchJobResults(props.taskName)
            alreadyDone.value = jobAlreadyDone(props.taskName)
        }
    })

    const submitDisabled = computed(() => !!taskData.value)

    function resetForm() {
        emit('resetForm')
    }

    async function submitForm(_: Event | undefined, confirmed=false){
        if (!selectedProject.value) return
        if(alreadyDone.value && !confirmed){
            showSubmissionConfirmation.value = true
            return
        }
        await spawnJob(props.taskName, props.formData || {})
    }

    return {
        props,
        alreadyDone,
        showSubmissionConfirmation,
        showAbortConfirmation,
        submitDisabled,
        taskData,
        resetForm,
        submitForm,
        abort,
    }
  }
}
</script>

<template>
    <div class="pa-3">
        <div v-if="taskData">
            <div v-if="taskData.message && !taskData.error" style="text-align: center;">{{ taskData.message }}</div>
            <div v-if="taskData.error" class="red--text" style="text-align: center;">Error: {{ taskData.error }}</div>
            <v-progress-linear v-else :value="taskData.percent_complete"/>
            <div v-if="!taskData.abort" class="d-flex pa-3" style="width:100%; justify-content:space-around">
                <v-btn color="red" @click="() => showAbortConfirmation = true">
                    Abort
                </v-btn>
            </div>
            <br />
        </div>
        <div style="display: flex; width: 100%; justify-content: space-between;">
            <v-btn @click="resetForm">Reset form</v-btn>
            <v-btn
                color="primary"
                :disabled="submitDisabled"
                @click="submitForm"
                style="float: right"
            >
                {{ alreadyDone ? 'Rerun': 'Run' }} {{ props.taskName }}
            </v-btn>
        </div>
        <v-dialog
            v-model="showSubmissionConfirmation"
            width="500"
        >
            <v-card>
                <v-card-title>
                Confirmation
                </v-card-title>

                <v-card-text>
                Are you sure you want to re-run the {{ props.taskName }} job?
                The previous results will be overwritten.
                </v-card-text>

                <v-divider></v-divider>

                <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                    text
                    @click="() => {showSubmissionConfirmation = false}"
                >
                    Cancel
                </v-btn>
                <v-btn
                    color="primary"
                    text
                    @click="() => {showSubmissionConfirmation = false, submitForm(undefined, true)}"
                >
                    Yes, Rerun
                </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog
            v-model="showAbortConfirmation"
            width="500"
        >
            <v-card>
                <v-card-title>
                Confirmation
                </v-card-title>

                <v-card-text>
                    Are you sure you want to abort this task? This will cancel any related tasks in this project.
                </v-card-text>

                <v-divider></v-divider>

                <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                    text
                    @click="() => {showAbortConfirmation = false}"
                >
                    Cancel
                </v-btn>
                <v-btn
                    color="red"
                    text
                    @click="() => {showAbortConfirmation = false, abort(taskData)}"
                >
                    Abort
                </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<style scoped>
.new-button {
    height: 100%!important;
    width: 150px;
}
</style>
