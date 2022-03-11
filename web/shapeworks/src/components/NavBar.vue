<script lang="ts">
import { defineComponent, computed } from '@vue/composition-api'
import { logout, oauthClient } from '@/api/auth';
import { selectedDataset, selectedSubject } from '../store';


export default defineComponent({
    setup() {
        const params = computed(() => ({
          dataset: selectedDataset.value?.id,
          subject: selectedSubject.value?.id,
        }))

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
            params,
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
        alt="ShapeWorks Logo"
        src="favicon.ico"
        transition="scale-transition"
        width="55px"
      />
      <v-toolbar-title class="text-h6">ShapeWorks</v-toolbar-title>
    </div>
    <v-tabs>
      <v-tab to="/">
        Select
      </v-tab>
      <v-tab :to="{name: 'data', params}" v-if="selectedDataset && selectedSubject">
        Data
      </v-tab>
      <v-tab :to="{name: 'groom', params}" v-if="selectedDataset && selectedSubject">
        Groom
      </v-tab>
      <v-tab :to="{name: 'optimize', params}" v-if="selectedDataset && selectedSubject">
        Optimize
      </v-tab>
      <v-tab :to="{name: 'analyze', params}" v-if="selectedDataset && selectedSubject">
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
