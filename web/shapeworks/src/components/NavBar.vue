<script lang="ts">
import { defineComponent, computed } from '@vue/composition-api'
import { logout, oauthClient } from '@/api/auth';
import { selectedDataset, selectedProject } from '../store';
import router from '@/router';


export default defineComponent({
    setup() {
      const params = computed(() => ({
        dataset: selectedDataset.value?.id,
      }))

      async function logInOrOut() {
          if (oauthClient.isLoggedIn) {
            await logout();
            window.location.reload();
          } else {
            oauthClient.redirectToLogin();
          }
      }

      function navigateToHome() {
        selectedDataset.value = undefined
        selectedProject.value = undefined
        router.push('/')
      }

      return {
          oauthClient,
          params,
          logInOrOut,
          selectedDataset,
          navigateToHome,
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
