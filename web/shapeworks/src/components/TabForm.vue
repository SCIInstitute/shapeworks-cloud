<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api'
import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
import VJsf from '@koumoul/vjsf'
import '@koumoul/vjsf/dist/main.css'
import Ajv from 'ajv';
import defaults from 'json-schema-defaults';
import { pollJobResults, spawnJob, jobAlreadyDone } from '../store';

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
    setup(props, context) {
        const ajv = new Ajv();
        const formDefaults = ref();
        const formData = ref({});
        const formSchema = ref();
        const formValid = ref(false);
        const refreshing = ref(false);
        const showSubmissionConfirmation = ref(false);
        const messages = ref('');
        const resultsPoll = ref();
        const reconstructionsPoll = ref();
        const alreadyDone = ref(jobAlreadyDone(props.form))

        async function fetchFormSchema() {
            formSchema.value = await (await fetch( `forms/${props.form}.json`)).json()
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
            if(alreadyDone.value && !confirmed){
                showSubmissionConfirmation.value = true
                return
            }
            const success = await spawnJob(props.form, formData.value)
            if(success){
                messages.value = `Successfully submitted ${props.form} job. Awaiting results...`
                resultsPoll.value = setInterval(
                    async () => {
                        const pollMessage = await pollJobResults(props.form)
                        if(pollMessage){
                            messages.value = pollMessage
                            setTimeout(() => messages.value = '', 5000)
                            clearInterval(resultsPoll.value)
                            context.emit("change")
                            alreadyDone.value = jobAlreadyDone(props.form)
                            resultsPoll.value = undefined
                            context.emit("change")
                        }
                    },
                    5000,
                )
                if(props.form === 'optimize'){
                    reconstructionsPoll.value = setInterval(
                        async () => {
                            const pollMessage = await pollJobResults('analyze')
                            if(pollMessage){
                                messages.value = pollMessage
                                setTimeout(() => messages.value = '', 5000)
                                clearInterval(reconstructionsPoll.value)
                                reconstructionsPoll.value = undefined
                                context.emit("change")
                            }
                        },
                        5000,
                    )
                }
            } else {
                messages.value = `Failed to submit ${props.form} job.`
                setTimeout(() => messages.value = '', 5000)
            }
        }

        return {
            props,
            formData,
            schemaOptions,
            formSchema,
            formValid,
            refreshing,
            showSubmissionConfirmation,
            messages,
            resetForm,
            submitForm,
            evaluateExpression,
            alreadyDone,
        }
    },
})
</script>


<template>
    <div>
        <div v-if="props.prerequisite()">
            <v-form v-model="formValid" class="pa-3">
                <div class="messages-box pa-3" v-if="messages.length">
                    {{ messages }}
                    <v-progress-circular
                        v-if="messages.includes('wait')"
                        indeterminate
                        color="primary"
                    ></v-progress-circular>
                </div>
                <div
                    v-if="props.form !== 'analyze'"
                    style="display: flex; width: 100%; justify-content: space-between;"
                >
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
                <div
                    v-if="props.form !== 'analyze'"
                    style="display: flex; width: 100%; justify-content: space-between;"
                >
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
</style>
