<script lang="ts">
/* eslint-disable no-unused-vars */
import {
    selectedProject,
    abort,
    deepSSMDataTab,
    deepSSMResult,
    deepSSMAugDataShown,
    groomFormData,
    optimizationFormData,
    loadDeepSSMDataForProject,
    deepSSMLoadingData,
    deepSSMErrorGlobalRange,
} from '@/store';
import { Ref, onMounted, ref, watch } from 'vue';
import { parseCSVFromURL } from '@/helper';
import TaskInfo from '../TaskInfo.vue';


export default {
  components: { TaskInfo },
    setup() {
        enum Sampler {
            Gaussian = "Gaussian",
            Mixture = "mixture",
            KDE = "KDE",
        }

        enum LossFunction {
            MSE = "MSE",
            Focal = "Focal",
        }

        const openExpansionPanel = ref<number>(0);
        const controlsTabs = ref();
        const showAbortConfirmation = ref(false);
        const formData = ref();
        const formDefaults = ref({});

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

        // headers are assigned from the parseCSV function's output
        const dataTables = {
            aug_table: ref<any>(undefined),
            aug_headers: ref<any>(undefined),
            training_table: ref<any>(undefined),
            training_headers: ref<any>([
                {text: "Training Stage", value: '0'},
                {text: "Epoch", value: '1'},
                {text: "LR", value: '2'},
                {text: "Train_Err", value: '3'},
                {text: "Train_Rel_Err", value: '4'},
                {text: "Val_Err", value: '5'},
                {text: "Val_Rel_Err", value: '6'},
                {text: "Sec", value: '7'},
            ]),
            testing_table: ref<any>(undefined),
            testing_headers: ref<any>([{text: "Name", value: '0'}, {text: "Distance", value: '1'}]),
        }

        /**
         * Converts an object of reactive properties to a plain object for use in api formData fields.
         */
        function getFormSection(object: {[key: string]: Ref<any>}) {
            return (
                Object.entries(object)
                    .map(([key, value]) => [key, value.value])
                    .reduce((obj, [key, value]) => {
                        obj[key] = value;
                        return obj;
                    }, {} as any)
            )
        }

        function getFormData() {
            const prepFormData = getFormSection(prepData);
            const augFormData = getFormSection(augmentationData);
            const trainFormData = getFormSection(trainingData);

            return {
                ...prepFormData,
                ...augFormData,
                ...trainFormData,
                ...groomFormData.value,
                ...optimizationFormData.value,
            }
        }

        function resetForm() {
            formData.value = formDefaults.value
            Object.entries(formData.value).forEach(([key, value]) => {
                if (prepData[key]) prepData[key].value = value
                if (augmentationData[key]) augmentationData[key].value = value
                if (trainingData[key]) trainingData[key].value = value
            })
        }

        function overwriteFormDefaultsFromProjectFile() {
            const file_contents = selectedProject.value?.file_contents
            if (file_contents) {
                const section = file_contents['deepssm']
                formDefaults.value = Object.fromEntries(
                    Object.entries(formDefaults.value).map(([key, value]) => {
                        if (section[key]) value = section[key]
                        if (value === "True") value = true
                        else if (value === "False") value = false
                        else if (typeof value === 'string' && !isNaN(parseFloat(value))) value = parseFloat(value)
                        return [key, value]
                    })
                )
            }
        }

        async function getCSVDataFromURL(url: string) {
            return await parseCSVFromURL(url);
        }

        onMounted(async () => {
            formDefaults.value = getFormData()
            overwriteFormDefaultsFromProjectFile()
            resetForm()
            if (!deepSSMResult.value && selectedProject.value) {
                deepSSMLoadingData.value = true;
                await loadDeepSSMDataForProject();
                deepSSMLoadingData.value = false;
            }
            if (deepSSMResult.value && deepSSMResult.value.result) {
                try {
                    Promise.all([
                        await getCSVDataFromURL(deepSSMResult.value.result.aug_total_data),
                        await getCSVDataFromURL(deepSSMResult.value.result.training_data_table),
                        await getCSVDataFromURL(deepSSMResult.value.result.testing_distances),
                    ]).then((res) => {
                        // get only the filename rather than the full path
                        const aug_values = res[0].map((row: any) => {
                            const newRow = {};
                            Object.keys(row).forEach((key: string) => {
                                const value = row[key];
                                if (typeof value === 'string') {
                                    newRow[key] = value.split('/').pop();
                                } else {
                                    newRow[key] = value;
                                }
                            });
                            return newRow;
                        });

                        dataTables.aug_table.value = aug_values;
                        dataTables.training_table.value = res[1];
                        dataTables.testing_table.value = res[2];

                        // Augmentation data table doesn't have headers, only a numbered list
                        dataTables.aug_headers.value = Object.keys(dataTables.aug_table.value[0]).map((_: string, index: number) => {
                            return {text: `${index+1}`, value: `${index}`}
                        });
                    });
                }
                catch (e) {
                    console.error(e);
                }
            }
        });

        watch(openExpansionPanel, () => {
            if (openExpansionPanel.value === 1 && deepSSMDataTab.value === -1) {
                deepSSMDataTab.value = 0;
            }
        });

        watch(deepSSMDataTab, () => {
            deepSSMErrorGlobalRange.value = [0, 1];
        });

        watch([ 
            augmentationData.aug_num_samples,
            augmentationData.aug_sampler_type,
            trainingData.train_loss_function,
            trainingData.train_epochs,
            trainingData.train_learning_rate,
            trainingData.train_batch_size,
            trainingData.train_decay_learning_rate,
            trainingData.train_fine_tuning,
            trainingData.train_fine_tuning_epochs,
            trainingData.train_fine_tuning_learning_rate,
         ], () => {
            formData.value = getFormData();
        })

        return {
            selectedProject,
            openExpansionPanel,
            controlsTabs,
            prepData,
            formData,
            resetForm,
            augmentationData,
            trainingData,
            Sampler,
            LossFunction,
            abort,
            showAbortConfirmation,
            deepSSMDataTab,
            deepSSMResult,
            deepSSMAugDataShown,
            deepSSMLoadingData,
            dataTables,
        }
    },
}
</script>

<template>
    <div class="pa-3">
        <task-info
            taskName="deepssm"
            :formData="formData"
            @resetForm="resetForm"
        />
        <div class="loading-dialog"><v-dialog v-model="deepSSMLoadingData" width="10%">Fetching results...  <v-progress-circular indeterminate align-center></v-progress-circular></v-dialog></div>
        <v-expansion-panels v-model="openExpansionPanel">
            <v-expansion-panel v-if="selectedProject && !selectedProject.readonly">
                <v-expansion-panel-header>Controls</v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-tabs v-model="controlsTabs">
                        <v-tab>Prep</v-tab>
                        <v-tab>Augmentation</v-tab>
                        <v-tab>Training</v-tab>
                    </v-tabs>
                    <v-tabs-items v-model="controlsTabs">
                        <v-tab-item>
                            <div>
                                <v-text-field v-model.number="prepData.testing_split.value" type="number" label="Test Split" suffix="%" />
                                <v-text-field v-model.number="prepData.validation_split.value" type="number" label="Validation Split" suffix="%" />
                                <v-text-field v-model.number="prepData.percent_variability.value" type="number" label="Percent Variablity Preserved" min="0.0" max="100.0" suffix="%" />
                                <div class="image-spacing">
                                    <v-label class="spacing-label">Image Spacing</v-label>
                                    <v-text-field class="spacing-input" v-model.number="prepData.image_spacing.value.x" type="number" label="X" />
                                    <v-text-field class="spacing-input" v-model.number="prepData.image_spacing.value.y" type="number" label="Y" />
                                    <v-text-field class="spacing-input" v-model.number="prepData.image_spacing.value.z" type="number" label="Z" />
                                </div>
                            </div>
                        </v-tab-item>
                        <v-tab-item>
                            <div>
                                <v-text-field v-model.number="augmentationData.aug_num_samples.value" type="number" label="Number of Samples" min="1" />

                                <v-select
                                    :items="Object.values(Sampler)"
                                    v-model="augmentationData.aug_sampler_type.value"
                                    label="Sampler Type"
                                />
                            </div>
                        </v-tab-item>
                        <v-tab-item>
                            <div>
                                <v-select
                                    :items="Object.values(LossFunction)"
                                    v-model="trainingData.train_loss_function.value"
                                    label="Loss Function"
                                />
                                <v-text-field v-model.number="trainingData.train_epochs.value" type="number" label="Epochs" min="0" />
                                <v-text-field v-model.number="trainingData.train_learning_rate.value" type="number" label="Learning Rate" min="0" />
                                <v-text-field v-model.number="trainingData.train_batch_size.value" type="number" label="Batch Size" min="1" />

                                <v-checkbox v-model="trainingData.train_decay_learning_rate.value" label="Decay Learning Rate"></v-checkbox>

                                <v-checkbox v-model="trainingData.train_fine_tuning.value" label="Fine Tuning"></v-checkbox>

                                <v-text-field v-model.number="trainingData.train_fine_tuning_epochs.value" :disabled="!trainingData.train_fine_tuning" type="number" label="Fine Tuning Epochs" min="1" />
                                <v-text-field v-model.number="trainingData.train_fine_tuning_learning_rate.value" :disabled="!trainingData.train_fine_tuning" type="number" label="Fine Tuning Learning Rate" min="0" />
                            </div>
                        </v-tab-item>
                    </v-tabs-items>
                </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel v-if="deepSSMResult && deepSSMResult.result">
                <v-expansion-panel-header>Data</v-expansion-panel-header>
                <v-expansion-panel-content>
                    <v-tabs v-model="deepSSMDataTab">
                        <v-tab>Augmentation</v-tab>
                        <v-tab>Training</v-tab>
                        <v-tab>Testing</v-tab>
                    </v-tabs>
                    <v-tabs-items v-model="deepSSMDataTab">
                        <v-tab-item>
                            <div>
                                <div class="aug-data-checkboxes">
                                    <v-radio-group v-model="deepSSMAugDataShown">
                                        <v-radio value="Original" label="Original Data"></v-radio>
                                        <v-radio value="Generated" label="Generated Data"></v-radio>
                                    </v-radio-group>
                                </div>
                                <v-data-table
                                    :items="dataTables.aug_table.value"
                                    :headers="dataTables.aug_headers.value"
                                />
                                <!-- violin plot -->
                                <h4>Violin Plot</h4>
                                <v-img :src="deepSSMResult.result?.aug_visualization" alt="Augmented Data Violin Plot" />
                            </div>
                        </v-tab-item>
                        <v-tab-item>
                            <div>
                                <v-data-table
                                    :items="dataTables.training_table.value"
                                    :headers="dataTables.training_headers.value"
                                />
                                <!-- epoch plots -->
                                Training Plot
                                <v-img :src="deepSSMResult.result?.training_visualization" alt="Training Plot" />
                                <div v-if="deepSSMResult.result?.training_visualization_ft">
                                    Fine Tuning Plot
                                    <v-img :src="deepSSMResult.result?.training_visualization_ft" alt="Fine Tuning Plot" />
                                </div>
                            </div>
                        </v-tab-item>
                        <v-tab-item>
                            <div>
                                <v-data-table
                                    :items="dataTables.testing_table.value"
                                    :headers="dataTables.testing_headers.value"
                                />
                            </div>
                        </v-tab-item>
                    </v-tabs-items>
                </v-expansion-panel-content>
            </v-expansion-panel>
        </v-expansion-panels>
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

.image-spacing, .aug-data-checkboxes {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0;
}
</style>
