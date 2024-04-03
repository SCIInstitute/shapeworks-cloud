<script lang="ts">
/* eslint-disable no-unused-vars */
import { loadDeepSSMDataForProject } from '@/store';
import {
    currentTasks,
    selectedProject,
    spawnJob,
    spawnJobProgressPoll,
    abort,
    deepSSMResult
} from '@/store';
import { Ref, computed, onMounted, ref, watch } from 'vue';


export default {
    setup() {
        enum Sampler {
            Gaussian = "Gaussian",
            Mixture = "Mixture",
            KDE = "KDE",
        }

        enum LossFunction {
            MSE = "MSE",
            Focal = "Focal",
        }

        const taskData = computed(
            () => {
                if (!selectedProject.value || !currentTasks.value[selectedProject.value.id]) return undefined
                return currentTasks.value[selectedProject.value.id]['deepssm_task']
            }
        )

        const openTab = ref<number>(0);
        const showAbortConfirmation = ref(false);

        const prepData = {
            testing_split: ref<number>(20),
            validation_split: ref<number>(20),
            percent_variability: ref<number>(95),
            image_spacing: ref<{x: number, y: number, z: number}>({x: 1, y: 1, z: 1})
        }
        
        // Augmentation
        const augmentationData = {
            aug_num_samples: ref<number>(300),
            aug_sampler_type : ref<Sampler>(Sampler.Gaussian),
        }
        
        // Training
        const trainingData = {
            train_loss_function: ref<LossFunction>(LossFunction.MSE),
            train_epochs: ref<number>(100),
            train_learning_rate: ref<number>(0.001),
            train_batch_size: ref<number>(8),
            train_decay_learning_rate: ref<boolean>(true),
            train_fine_tuning: ref<boolean>(true),
            train_fine_tuning_epochs: ref<number>(100),
            train_fine_tuning_learning_rate: ref<number>(0.001),
        }

        /**
         * Converts an object of reactive properties to a plain object for use in api formData fields.
         */
        function getFormData(object: {[key: string]: Ref<any>}) {
            return (
                Object.entries(object)
                    .map(([key, value]) => [key, value.value])
                    .reduce((obj, [key, value]) => {
                        obj[key] = value;
                        return obj;
                    }, {} as any)
            )
        }

        async function submitDeepSSMJob() {
            if (!selectedProject.value) return;

            const prepFormData = getFormData(prepData);
            const augFormData = getFormData(augmentationData);
            const trainFormData = getFormData(trainingData);
            const formData = {
                ...prepFormData,
                ...augFormData,
                ...trainFormData,
            }

            const taskId = await spawnJob("deepssm", formData);
            currentTasks.value[selectedProject.value.id] = taskId;

            spawnJobProgressPoll();
            return taskId;
        }

        const tabs = ref();

        onMounted(async () => {
            if (!deepSSMResult.value && selectedProject.value) {
                await loadDeepSSMDataForProject();
            }
        })

        return {
            openTab,
            prepData,
            augmentationData,
            trainingData,
            Sampler,
            LossFunction,
            submitDeepSSMJob,
            taskData,
            abort,
            showAbortConfirmation,
            tabs,
            deepSSMResult,
        }
    },
}
</script>

<template>
    <div v-if="taskData" class="messages-box pa-3">
        Running DeepSSM process...
        <div v-if="taskData.error">{{ taskData.error }}</div>
        <v-progress-linear v-else :value="taskData.percent_complete"/>
        <div class="d-flex pa-3" style="width:100%; justify-content:space-around">
            <v-btn
                color="red"
                @click="() => showAbortConfirmation = true"
            >
                Abort
            </v-btn>
        </div>
        <br />
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
                    @click="() => {
                        showAbortConfirmation = false;
                        if (taskData) {
                            abort(taskData)
                        }
                    }"
                >
                    Abort
                </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
    <div class="pa-3" v-else>
        <v-tabs v-model="tabs">
            <v-tab>Controls</v-tab>
            <v-tab v-if="deepSSMResult">Data</v-tab>
        </v-tabs>
        <v-tabs-items v-model="tabs">
            <v-tab-item>
                <v-expansion-panels v-model="openTab">
                    <v-expansion-panel>
                        <v-expansion-panel-header>
                            Prep
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                            <v-text-field v-model="prepData.testing_split" type="number" label="Test Split" suffix="%" />
                            <v-text-field v-model="prepData.validation_split" type="number" label="Validation Split" suffix="%" />
                            <v-text-field v-model="prepData.percent_variability" type="number" label="Percent Variablity Preserved" min="0" max="100" suffix="%" />
                            <div class="image-spacing">
                                <v-label class="spacing-label">Image Spacing</v-label>
                                <v-text-field class="spacing-input" v-model="prepData.image_spacing.value.x" type="number" label="X" />
                                <v-text-field class="spacing-input" v-model="prepData.image_spacing.value.y" type="number" label="Y" />
                                <v-text-field class="spacing-input" v-model="prepData.image_spacing.value.z" type="number" label="Z" />
                            </div>
                        </v-expansion-panel-content>
                    </v-expansion-panel>
                    <v-expansion-panel>
                        <v-expansion-panel-header>
                            Augmentation
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                            <v-text-field v-model="augmentationData.aug_num_samples.value" type="number" label="Number of Samples" min="1" />

                            <v-select 
                                :items="Object.values(Sampler)"
                                v-model="augmentationData.aug_sampler_type"
                                label="Sampler Type"
                            />
                            <!-- needs sub-panel for data -->
                        </v-expansion-panel-content>
                    </v-expansion-panel>
                    <v-expansion-panel>
                        <v-expansion-panel-header>
                            Training
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                            <v-select 
                                :items="Object.values(LossFunction)"
                                v-model="trainingData.train_loss_function"
                                label="Loss Function"
                            />
                            <v-text-field v-model="trainingData.train_epochs.value" type="number" label="Epochs" min="0" />
                            <v-text-field v-model="trainingData.train_learning_rate.value" type="number" label="Learning Rate" min="0" />
                            <v-text-field v-model="trainingData.train_batch_size.value" type="number" label="Batch Size" min="1" />

                            <v-checkbox v-model="trainingData.train_decay_learning_rate" label="Decay Learning Rate"></v-checkbox>

                            <v-checkbox v-model="trainingData.train_fine_tuning" label="Fine Tuning"></v-checkbox>

                            <v-text-field v-model="trainingData.train_fine_tuning_epochs.value" :disabled="!trainingData.train_fine_tuning" type="number" label="Fine Tuning Epochs" min="1" />
                            <v-text-field v-model="trainingData.train_fine_tuning_learning_rate.value" :disabled="!trainingData.train_fine_tuning" type="number" label="Fine Tuning Learning Rate" min="0" />
                        </v-expansion-panel-content>
                    </v-expansion-panel>
                    <v-expansion-panel>
                        <v-expansion-panel-header>
                            Testing
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                            <!-- Data table for name and average distance -->
                        </v-expansion-panel-content>
                    </v-expansion-panel>
                </v-expansion-panels>
                <v-btn @click="submitDeepSSMJob">Run DeepSSM tasks</v-btn>
            </v-tab-item>
            <v-tab-item v-if="deepSSMResult">
                <v-expansion-panels>
                    <v-expansion-panel>
                        <v-expansion-panel-header>
                            Augmentation
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                            <!-- table -->
                            total
                            <!-- violin plot -->
                            <v-img :src="deepSSMResult.result?.aug_visualization" alt="Augmented Data Violin Plot" />
                        </v-expansion-panel-content>
                    </v-expansion-panel>
                    <v-expansion-panel>
                        <v-expansion-panel-header>
                            Training
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                            <!-- training data -->
                            <!-- table -->
                            <!-- epoch plots -->
                            Training Plot
                            <v-img :src="deepSSMResult.result?.training_visualization" alt="Training Plot" />
                            <div v-if="deepSSMResult.result?.training_visualization_ft">
                                Fine Tuning Plot
                                <v-img :src="deepSSMResult.result?.training_visualization_ft" alt="Fine Tuning Plot" />
                            </div>
                        </v-expansion-panel-content>
                    </v-expansion-panel>
                    <v-expansion-panel>
                        <v-expansion-panel-header>
                            Testing
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                            <!-- testing data -->
                            <!-- distance table -->
                        </v-expansion-panel-content>
                    </v-expansion-panel>
                </v-expansion-panels>
            </v-tab-item>
        </v-tabs-items>
    </div>
</template>

<style>
input::-webkit-outer-spin-button, 
input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

input[type=number] {
    appearance: textfield;
    -moz-appearance: textfield;
}

.spacing-label {
    margin-bottom: 0;
}

.spacing-input {
    margin-bottom: 0;
    width: 6%;
    margin: 0 10px;
}

.image-spacing {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0;
}
</style>
