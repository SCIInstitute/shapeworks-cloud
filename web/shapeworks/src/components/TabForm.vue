<script>
import { defineComponent, ref } from '@vue/composition-api'
import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
import VJsf from '@koumoul/vjsf'
import '@koumoul/vjsf/dist/main.css'
import Ajv from 'ajv';
import defaults from 'json-schema-defaults';
import { submitForm } from '../store';

Vue.use(Vuetify)


export default defineComponent({
    props: {
        form: {
            type: String,
            required: true,
        }
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

        async function fetchFormSchema() {
            formSchema.value = await (await fetch( `forms/${props.form}.json`)).json()
            formDefaults.value = defaults(formSchema.value)
        }
        fetchFormSchema()

        function evaluateExpression (expression) {
            if(expression){
                // The shemas are trusted source code
                expression = eval(expression)
                return expression(formData.value)
            }
            return true;
        }

        const schemaOptions = {
            rootDisplay: "expansion-panels",
            autoFocus: true,
            ajv,
            sliderProps: {
                thumbLabel: true
            }
        }

        function resetForm () {
            refreshing.value = true;
            formData.value = formDefaults.value;
            setTimeout(() => { refreshing.value = false; }, 1)
        }

        return {
            props,
            formData,
            schemaOptions,
            formSchema,
            formValid,
            refreshing,
            resetForm,
            submitForm,
            evaluateExpression,
        }
    },
})
</script>


<template>
<v-form v-model="formValid" class="pa-3" >
    <div style="display: flex; width: 100%; justify-content: space-between;">
        <v-btn @click="resetForm">Restore defaults</v-btn>
        <v-btn color="primary" @click="() => { submitForm(props.form, formData) }">{{ props.form }}</v-btn>
    </div>
    <br />
    <v-jsf
      v-if="formSchema && !refreshing"
      v-model="formData"
      :schema="formSchema"
      :options="schemaOptions"
    >
        <!-- TODO: figure out recursive slot definition -->
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
        <v-btn color="primary" @click="() => { submitForm(props.form, formData) }">{{ props.form }}</v-btn>
    </div>
    <br>
</v-form>
</template>
