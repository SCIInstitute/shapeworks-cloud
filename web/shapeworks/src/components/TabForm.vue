<script>
import { defineComponent, ref } from '@vue/composition-api'
import Vue from 'vue'
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
import VJsf from '@koumoul/vjsf'
import '@koumoul/vjsf/dist/main.css'

Vue.use(Vuetify)


export default defineComponent({
    props: {
        formFile: {
            type: String,
            required: true,
        }
    },
    components: {
      VJsf,
    },
    setup(props) {
        const formData = ref({});
        const formSchema = ref();
        const formValid = ref(false);

        async function fetchFormSchema() {
            formSchema.value = await (await fetch( `forms/${props.formFile}`)).json()
        }
        fetchFormSchema()

        const schemaOptions = {
            disableAll: false,
            autoFoldObjects: true,
            rootDisplay: "expansion-panels",
            objectContainerClass: "pa-3",
        }

        return {
            formData,
            schemaOptions,
            formSchema,
            formValid,
        }
    },
})
</script>


<template>
<v-form v-model="formValid">
    <v-jsf
      v-if="formSchema"
      v-model="formData"
      :schema="formSchema"
      :options="schemaOptions"
    />
</v-form>
</template>
