<template>
  <v-app>
    <nav-bar />
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
import NavBar from './components/NavBar';

export default {
  components: {
    NavBar,
  },
};
</script>

<style>
html {
  height: 100vh;
  overflow-y: hidden !important;
}
</style>
