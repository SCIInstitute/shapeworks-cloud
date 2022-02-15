<script>
import { defineComponent } from '@vue/composition-api'
import NavBar from './components/NavBar';
import { oauthClient } from './api/auth';

export default defineComponent({
  components: {
    NavBar,
  },
  setup() {
    const logIn = () => {
      oauthClient.redirectToLogin();
    }
    return {
      oauthClient,
      logIn,
    }
  },
});
</script>

<template>
  <v-app>
    <nav-bar />
    <v-main>
      <router-view />
    </v-main>

    <v-overlay
      absolute
      :value="!oauthClient.isLoggedIn"
      :opacity="0.8"
      style="margin-top: -30vh"
    >
      <v-btn
        color="primary"
        @click="logIn"
      >
        Log in to Continue
      </v-btn>
    </v-overlay>
  </v-app>
</template>

<style>
html {
  height: 100vh;
  overflow-y: hidden !important;
}
</style>
