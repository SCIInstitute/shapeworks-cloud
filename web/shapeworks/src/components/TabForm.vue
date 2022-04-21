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

        const schemaOptions = {
            rootDisplay: "expansion-panels",
            ajv,
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
        }
    },
})
</script>


<template>
<v-form v-model="formValid" class="pa-3">
    <div style="display: flex; width: 100%; justify-content: space-between;">
        <v-btn @click="resetForm">Restore defaults</v-btn>
        <v-btn @click="() => { submitForm(props.form, formData) }">Run {{ props.form }}</v-btn>
    </div>
    <br>
    <v-jsf
      v-if="formSchema && !refreshing"
      v-model="formData"
      :schema="formSchema"
      :options="schemaOptions"
    />
</v-form>
</template>
