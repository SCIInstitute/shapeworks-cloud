<script lang="ts">
import { defineComponent, onMounted, computed } from '@vue/composition-api'
import { logout, oauthClient } from '@/api/auth';
import { selectedDataset, selectedSubject, loadingState } from '../store';
import router from '@/router';
import { getDataset, getSubject } from '@/api/rest';


export default defineComponent({
    setup() {
        onMounted(async () => {
            let datasetId: string = router.currentRoute.query.dataset as string;
            let subjectId: string = router.currentRoute.query.subject as string;
            if (!(datasetId && subjectId)) return;
            loadingState.value = true;
            selectedDataset.value = await getDataset(datasetId);
            selectedSubject.value = await getSubject(subjectId);
            loadingState.value = false;
        })

        const queryParams = computed(() => {
          if(selectedDataset.value && selectedSubject.value){
            `?dataset=${selectedDataset.value.id}}&subject=${selectedSubject.value.id}`
          } else {
            return '';
          }
        })

        const logInOrOut = async() => {
            if (oauthClient.isLoggedIn) {
              await logout();
              window.location.reload();
            } else {
              oauthClient.redirectToLogin();
            }
        }

        return {
            oauthClient,
            queryParams,
            logInOrOut,
            selectedDataset,
            selectedSubject,
        }
    }
})
</script>

<template>
  <v-app-bar app height="80px">
    <div class="d-flex align-center px-5">
      <v-img
        alt="Shapeworks Logo"
        src="favicon.ico"
        transition="scale-transition"
        width="55px"
      />
      <v-toolbar-title class="text-h6">Shapeworks</v-toolbar-title>
    </div>
    <v-tabs>
      <v-tab to="/">
        Select
      </v-tab>
      <v-tab to="/data" v-if="selectedDataset && selectedSubject">
        Data
      </v-tab>
      <v-tab to="/groom" v-if="selectedDataset && selectedSubject">
        Groom
      </v-tab>
      <v-tab to="/optimize" v-if="selectedDataset && selectedSubject">
        Optimize
      </v-tab>
      <v-tab to="/analyze" v-if="selectedDataset && selectedSubject">
        Analyze
      </v-tab>
      <v-tab to="/demo">
        Demo
      </v-tab>
    </v-tabs>
    <v-spacer />
    <v-btn
    v-if="oauthClient.isLoggedIn"
      text
      @click="logInOrOut"
    >
      Logout
    </v-btn>

  </v-app-bar>
</template>

<style>
</style>
