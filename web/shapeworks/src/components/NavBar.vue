<script lang="ts">
import { defineComponent, inject } from '@vue/composition-api'
import OAuthClient from '@girder/oauth-client';


export default defineComponent({
  setup() {
    const oauthClient = inject<OAuthClient>('oauthClient');
    if (oauthClient === undefined) {
      throw new Error('Must provide "oauthClient" into component.');
    }

    const logInOrOut = () => {
      if (oauthClient.isLoggedIn) {
        // TODO: this doesn't clear cookies and local storage,
        // so our session is still restorable after logout
        oauthClient.logout();
      } else {
        oauthClient.redirectToLogin();
      }
    }

    return {
      oauthClient,
      logInOrOut,
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
      <v-tab to="/data">
        Data
      </v-tab>
      <v-tab to="/groom">
        Groom
      </v-tab>
      <v-tab to="/optimize">
        Optimize
      </v-tab>
      <v-tab to="/analyze">
        Analyze
      </v-tab>
      <v-tab to="/">
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
