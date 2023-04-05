<script lang="ts">
import { defineComponent, ref, computed } from '@vue/composition-api'
import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
import VJsf from '@koumoul/vjsf'
import '@koumoul/vjsf/dist/main.css'
import Ajv from 'ajv';
import defaults from 'json-schema-defaults';
import {
    spawnJob, jobAlreadyDone,
    allDataObjectsInDataset, currentTasks,
    spawnJobProgressPoll, selectedProject, abort
} from '@/store';
import { DataObject } from '../types/index';

Vue.use(Vuetify)


export default defineComponent({
    props: {
        form: {
            type: String,
            required: true,
        },
        prerequisite: {
            type: Function,
            default: () => true
        },
        prerequisite_unfulfilled: {
            type: String,
            required: false,
        },
    },
    components: {
        VJsf,
    },
    setup(props) {
        const ajv = new Ajv();
        const formDefaults = ref();
        const formData = ref({});
        const formSchema = ref();
        const formValid = ref(false);
        const refreshing = ref(false);
        const showSubmissionConfirmation = ref(false);
        const showAbortConfirmation = ref(false);
        const messages = ref('');
        const alreadyDone = ref(jobAlreadyDone(props.form))

        async function fetchFormSchema() {
            let formName = props.form
            if(formName === 'groom'){
                const types = allDataObjectsInDataset.value.map((obj: DataObject) => obj.type)
                if(types.some((type: string) => type === 'segmentation')) {
                    formName += '_segmentation'
                } else {
                    formName += '_mesh'
                }
            }

            formSchema.value = await (await fetch( `forms/${formName}.json`)).json()
            formDefaults.value = defaults(formSchema.value)
        }
        fetchFormSchema()

        function evaluateExpression (expression: string) {
            if(expression){
                // The shemas are trusted source code
                const expressionFunc = eval(expression)
                return expressionFunc(formData.value)
            }
            return true;
        }

        const schemaOptions = {
            rootDisplay: "expansion-panels",
            autoFocus: true,
            ajv,
            sliderProps: {
                thumbLabel: true
            },
            tooltipProps: {
                openOnHover: true,
                top: true
            }
        }

        function resetForm () {
            refreshing.value = true;
            formData.value = formDefaults.value;
            setTimeout(() => { refreshing.value = false; }, 1)
        }

        async function submitForm(_: Event, confirmed=false){
            if (!selectedProject.value) return
            if (!currentTasks.value[selectedProject.value.id]) {
                currentTasks.value[selectedProject.value.id] = {}
            }
            if(alreadyDone.value && !confirmed){
                showSubmissionConfirmation.value = true
                return
            }
            const taskIds = await spawnJob(props.form, formData.value)
            if(!taskIds || taskIds.length === 0) {
                messages.value = `Failed to submit ${props.form} job.`
                setTimeout(() => messages.value = '', 10000)
            } else {
                messages.value = `Successfully submitted ${props.form} job. Awaiting results...`
                currentTasks.value[selectedProject.value.id] = taskIds
                spawnJobProgressPoll()
            }
        }

        const taskData = computed(
            () => {
                if(!selectedProject.value?.id ||
                !currentTasks.value[selectedProject.value.id]) return undefined
                return currentTasks.value[selectedProject.value.id][`${props.form}_task`]
            }
        )


        return {
            props,
            formData,
            schemaOptions,
            formSchema,
            formValid,
            refreshing,
            showSubmissionConfirmation,
            showAbortConfirmation,
            messages,
            resetForm,
            submitForm,
            evaluateExpression,
            alreadyDone,
            taskData,
            abort,
        }
    },
})
</script>


<template>
    <div>
        <div v-if="props.prerequisite()">
            <v-form v-model="formValid" class="pa-3">
                <div v-if="taskData">
                    <div class="messages-box pa-3" v-if="messages.length">
                        {{ messages }}
                    </div>
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
                </div>
                <div style="display: flex; width: 100%; justify-content: space-between;">
                    <v-btn @click="resetForm">Restore defaults</v-btn>
                    <v-btn color="primary" @click="submitForm">
                        {{ alreadyDone ? 're': '' }}{{ props.form }}
                    </v-btn>
                </div>
                <br />
                <v-jsf
                v-if="formSchema && !refreshing"
                v-model="formData"
                :schema="formSchema"
                :options="schemaOptions"
                >
                    <template slot="custom-conditional" slot-scope="context">
                        <v-jsf
                            v-if="evaluateExpression(context.schema['x-display-if'])"
                            v-model="formData[context.fullKey.split('.')[0]][context.fullKey.split('.')[1]]"
                            v-bind="context"
                        >
                            <template slot="custom-readonly" slot-scope="context">
                                <div style="display: flex; width: 100%; justify-content: space-between;">
                                    <p>{{ context.label }}</p>
                                    <p>{{ context.value }}{{ context.schema['x-display-append'] }}</p>
                                </div>
                            </template>
                        </v-jsf>
                    </template>
                </v-jsf>
                <br />
                <div style="display: flex; width: 100%; justify-content: space-between;">
                    <v-btn @click="resetForm">Restore defaults</v-btn>
                    <v-btn color="primary" @click="submitForm">
                        {{ alreadyDone ? 're': '' }}{{ props.form }}
                    </v-btn>
                </div>
                <br>
                <v-dialog
                v-model="showSubmissionConfirmation"
                width="500"
                >
                    <v-card>
                        <v-card-title>
                        Confirmation
                        </v-card-title>

                        <v-card-text>
                        Are you sure you want to re-run the {{ props.form }} job?
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
                            @click="() => {showSubmissionConfirmation = false, submitForm(undefined, confirmed=true)}"
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
            </v-form>
        </div>
        <div v-else-if="props.prerequisite_unfulfilled" class="pa-5">
            {{ props.prerequisite_unfulfilled }}
        </div>
    </div>
</template>

<style lang="css">
.messages-box {
    text-align: center;
    color: #2196f3;
}
.float-right {
    float: right;
}
.col-6 {
    max-width: 100% !important;
    padding: 0px 20px !important;
}
</style>
