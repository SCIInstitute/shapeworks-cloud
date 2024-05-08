<script lang="ts">
import { ref, watch } from 'vue'
import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
import VJsf from '@koumoul/vjsf'
import '@koumoul/vjsf/dist/main.css'
import Ajv from 'ajv';
import defaults from 'json-schema-defaults';
import {
    allDataObjectsInDataset, groomFormData, optimizationFormData, selectedProject,
} from '@/store';
import { DataObject } from '../types/index';
import TaskInfo from './TaskInfo.vue'

Vue.use(Vuetify)


export default {
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
        TaskInfo,
    },
    setup(props) {
        const ajv = new Ajv();
        const formDefaults = ref();
        const formData = ref({});
        const formSchema = ref();
        const formValid = ref(false);

        function overwriteFormDefaultsFromProjectFile() {
            const file_contents = selectedProject.value?.file_contents
            if (file_contents) {
                const newDefaults = {}
                const parseNewDefaults = (data: Object) => {
                    if (data) {
                        Object.entries(data).forEach(([key, value]) => {
                            if (value === "True") value = true
                            else if (value === "False") value = false
                            else if (typeof value === 'string' && !isNaN(parseFloat(value))) value = parseFloat(value)
                            newDefaults[key] = value
                        })
                    }
                }

                const section = file_contents[props.form]
                if (section && props.form === 'groom') {
                    // section organized by anatomies, pick first
                    const data = Object.values(section)[0] as Object
                    if (data) parseNewDefaults(data)
                } else if (section && props.form === 'optimize') {
                    parseNewDefaults(section)
                }
                formDefaults.value = Object.fromEntries(
                    Object.entries(formDefaults.value).map(([sName, sData]: [string, any]) => {
                        if (!sData) return [sName, sData]
                        return [sName, Object.fromEntries(
                            Object.entries(sData).map(([key, value]) => {
                                if (newDefaults[key]) return [key, newDefaults[key]]
                                return [key, value]
                            })
                        )]
                    })
                )
            }
        }

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
            overwriteFormDefaultsFromProjectFile()

            formData.value = formDefaults.value
        }
        fetchFormSchema()

        function evaluateExpression (expression: string) {
            if(expression){
                // The schemas are trusted source code
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

        function simplifyFormData(formData) {
            let payload;
            Object.keys(formData).forEach((key) => {
                if (key.includes("section") || key.includes("analysis")) {
                    const value = formData[key]
                    payload = {
                        ...payload,
                        ...value,
                    }
                } else {
                    payload[key] = formData[key]
                }
            })
            return payload
        }

        watch(formData, () => {
            const payload = simplifyFormData(formData.value)
            if (props.form === 'optimize') {
                optimizationFormData.value = payload
            } else if (props.form === 'groom') {
                groomFormData.value = payload
            }
        }, {deep:true})

        function resetForm() {
            formData.value = formDefaults.value
        }

        return {
            props,
            schemaOptions,
            formData,
            formDefaults,
            formSchema,
            formValid,
            simplifyFormData,
            resetForm,
            evaluateExpression,
        }
    },
}
</script>


<template>
    <div>
        <div v-if="props.prerequisite()">
            <task-info
                :taskName="props.form"
                :formData="simplifyFormData(formData)"
                @resetForm="resetForm"
            />
            <v-form v-model="formValid" class="pa-3">
                <v-jsf
                    v-if="formSchema && formData"
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
            </v-form>
        </div>
        <div v-else>{{ props.prerequisite_unfulfilled }}</div>
    </div>
</template>

<style lang="css">
.float-right {
    float: right;
}
.col-6 {
    max-width: 100% !important;
    padding: 0px 20px !important;
}
</style>
