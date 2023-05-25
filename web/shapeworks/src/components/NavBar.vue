<script lang="ts">
import { defineComponent, computed } from '@vue/composition-api'
import { logout, oauthClient } from '@/api/auth';
import { allDatasets, loadingState, selectedDataset, selectedProject } from '@/store';
import FilterSearch from './FilterSearch.vue';
import router from '@/router';
import { getDatasets } from '@/api/rest';


export default defineComponent({
    components: {
      FilterSearch
    },
    setup() {
      const params = computed(() => ({
        dataset: selectedDataset.value?.id,
        project: selectedProject.value?.id
      }))

      async function logInOrOut() {
          if (oauthClient.isLoggedIn) {
            await logout();
            window.location.reload();
          } else {
            oauthClient.redirectToLogin();
          }
      }

      async function navigateToHome() {
        selectedDataset.value = undefined
        selectedProject.value = undefined
        if (router.currentRoute.path !== '/') {
          router.push('/')
        }
        loadingState.value = true;
        allDatasets.value = (await getDatasets(undefined)).sort((a, b) => {
            if(a.created < b.created) return 1;
            if(a.created > b.created) return -1;
            return 0;
        });
        loadingState.value = false;
      }

      return {
          oauthClient,
          params,
          logInOrOut,
          selectedDataset,
          selectedProject,
          navigateToHome,
          router,
      }
    }
})
</script>

<template>
  <v-app-bar app height="50px">
    <div class="d-flex align-center px-5" @click="navigateToHome">
      <v-img
        alt="ShapeWorks Logo"
        src="favicon.ico"
        transition="scale-transition"
        width="55px"
      />
      <v-toolbar-title class="text-h6">ShapeWorks</v-toolbar-title>
    </div>
    <v-spacer />
    <filter-search v-if="!(selectedDataset && selectedProject) && !(router.currentRoute.params.dataset && router.currentRoute.params.project)"/>
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
.router-link-active {
  color: white!important;
  text-decoration: none!important;
}
</style>
