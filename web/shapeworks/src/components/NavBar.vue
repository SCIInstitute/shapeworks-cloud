<script lang="ts">
import { defineComponent } from '@vue/composition-api'
import { logout, oauthClient } from '@/api/auth';
import { selectedDataset, selectedSubject } from '../store/index';


export default defineComponent({
  setup() {
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
      logInOrOut,
      selectedDataset,
      selectedSubject,
    }
  }
})
</script>

<template>
  <v-app-bar app>
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
