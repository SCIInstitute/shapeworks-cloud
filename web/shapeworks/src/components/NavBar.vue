<script lang="ts">
export default {}
</script>

<template>
  <v-app-bar
    app
    color="primary"
    dark
  >
    <div class="d-flex align-center">
      <v-img
        alt="Vuetify Logo"
        class="shrink mr-2"
        contain
        src="https://cdn.vuetifyjs.com/images/logos/vuetify-logo-dark.png"
        transition="scale-transition"
        width="40"
      />

      <v-img
        alt="Vuetify Name"
        class="shrink mt-1 hidden-sm-and-down"
        contain
        min-width="100"
        src="https://cdn.vuetifyjs.com/images/logos/vuetify-name-dark.png"
        width="100"
      />
    </div>
    <v-tabs>
      <v-tab to="data">
        Data
      </v-tab>
      <v-tab to="groom">
        Groom
      </v-tab>
      <v-tab to="optimize">
        Optimize
      </v-tab>
      <v-tab to="analyze">
        Analyze
      </v-tab>
      <v-tab to="demo">
        Demo
      </v-tab>
    </v-tabs>
  </v-app-bar>
</template>

<style>
</style>
