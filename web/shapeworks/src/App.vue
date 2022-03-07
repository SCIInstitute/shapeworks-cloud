<script>
import { defineComponent } from '@vue/composition-api'
import NavBar from './components/NavBar';
import { oauthClient } from './api/auth';
import { loadingState } from './store';

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
            loadingState,
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
        >
            <v-btn
                color="primary"
                @click="logIn"
            >
              Log in to Continue
            </v-btn>
        </v-overlay>

        <v-overlay
            absolute
            :value="loadingState"
            :opacity="0.8"
        >
            <v-card flat width="200px">
              <v-progress-linear
                indeterminate
                color="white"
                class="mb-0"
              ></v-progress-linear>
          </v-card>
        </v-overlay>
    </v-app>
</template>

<style>
html {
    overflow-y: auto !important;
}
.v-overlay {
    top: -100%!important;
}
.v-overlay__content {
    top: 50vh;
}
</style>
