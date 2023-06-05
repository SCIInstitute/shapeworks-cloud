<script>
import { defineComponent } from 'vue'
import NavBar from './components/NavBar';
import { oauthClient } from './api/auth';
import { loadingState, currentError } from './store';

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
            currentError,
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

        <v-overlay
            absolute
            :value="currentError !== undefined"
            :opacity="0.8"
        >
            <v-card class="pa-5">
                <v-btn
                    icon
                    @click.stop="currentError = undefined"
                    class="pa-3"
                    style="float:right"
                >
                    <v-icon>mdi-close</v-icon>
                </v-btn>
                <v-card-title>
                    Error:
                </v-card-title>
                <v-card-text v-if="currentError && currentError.length">
                    {{ currentError }}
                </v-card-text>
                <v-card-text v-else>
                    An error has occurred.
                </v-card-text>
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
