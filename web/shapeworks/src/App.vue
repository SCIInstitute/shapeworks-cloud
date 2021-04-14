<template>
  <v-app>
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

      <v-spacer></v-spacer>

      <v-btn
        href="https://github.com/vuetifyjs/vuetify/releases/latest"
        target="_blank"
        text
      >
        <span class="mr-2">Latest Release</span>
        <v-icon>mdi-open-in-new</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <shape-viewer
        :data="shapeData"
        :rows="rows"
        :columns="columns"
        :glyph-size="glyphSize"
      />
    </v-main>
  </v-app>
</template>

<script>
import ShapeViewer from './components/ShapeViewer';
import shapeReader from './reader/shape';
import pointsReader from './reader/points';

const SHAPE_URL = 'https://data.kitware.com/api/v1/file/60774afa2fa25629b9c4d14e/download'
const POINTS_URL = 'https://data.kitware.com/api/v1/file/60774bd32fa25629b9c4d1e2/download'

export default {
  components: {
    ShapeViewer,
  },
  data() {
    return {
      rows: 3,
      columns: 4,
      shapeData: [],
      glyphSize: 1.5
    };
  },
  created() {
    this.loadData();
  },
  methods: {
    async loadData() {
      const [shape, points] = await Promise.all([
        shapeReader(SHAPE_URL),
        pointsReader(POINTS_URL),
      ]);

      this.shapeData.length = 0;
      for (let i = 0; i < 15; i += 1) {
        this.shapeData.push({
          points,
          shape,
        });
      }
    },
  },
};
</script>

<style>
html {
  height: 100vh;
  overflow-y: hidden !important;
}
</style>
