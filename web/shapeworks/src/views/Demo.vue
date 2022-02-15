<script lang="ts">
import { defineComponent, onMounted, ref } from '@vue/composition-api'

import ShapeViewer from '../components/ShapeViewer.vue';
import shapeReader from '../reader/shape';
import pointsReader from '../reader/points';
import { ShapeData } from '../types';

const SHAPE_URLS = [
  'https://data.kitware.com/api/v1/item/6086c7282fa25629b9389550/download',
  'https://data.kitware.com/api/v1/item/6086c7282fa25629b9389548/download',
  'https://data.kitware.com/api/v1/item/6086c7282fa25629b9389540/download',
  'https://data.kitware.com/api/v1/item/6086c7272fa25629b9389538/download',
  'https://data.kitware.com/api/v1/item/6086c7272fa25629b9389530/download',
  'https://data.kitware.com/api/v1/item/6086c7272fa25629b9389528/download',
  'https://data.kitware.com/api/v1/item/6086c7272fa25629b9389520/download',
  'https://data.kitware.com/api/v1/item/6086c7262fa25629b9389518/download',
  'https://data.kitware.com/api/v1/item/6086c7262fa25629b9389510/download',
  'https://data.kitware.com/api/v1/item/6086c7262fa25629b9389508/download',
  'https://data.kitware.com/api/v1/item/6086c7252fa25629b9389500/download',
  'https://data.kitware.com/api/v1/item/6086c7252fa25629b93894f8/download',
  'https://data.kitware.com/api/v1/item/6086c7252fa25629b93894f0/download',
  'https://data.kitware.com/api/v1/item/6086c7242fa25629b93894e8/download',
  'https://data.kitware.com/api/v1/item/6086c7242fa25629b93894e0/download',
];

const POINTS_URLS = [
  'https://data.kitware.com/api/v1/item/6086c6382fa25629b9389496/download',
  'https://data.kitware.com/api/v1/item/6086c6382fa25629b938948e/download',
  'https://data.kitware.com/api/v1/item/6086c6382fa25629b9389486/download',
  'https://data.kitware.com/api/v1/item/6086c6382fa25629b938947e/download',
  'https://data.kitware.com/api/v1/item/6086c6382fa25629b9389476/download',
  'https://data.kitware.com/api/v1/item/6086c6372fa25629b938946e/download',
  'https://data.kitware.com/api/v1/item/6086c6372fa25629b9389466/download',
  'https://data.kitware.com/api/v1/item/6086c6372fa25629b938945e/download',
  'https://data.kitware.com/api/v1/item/6086c6372fa25629b9389456/download',
  'https://data.kitware.com/api/v1/item/6086c6362fa25629b938944e/download',
  'https://data.kitware.com/api/v1/item/6086c6362fa25629b9389446/download',
  'https://data.kitware.com/api/v1/item/6086c6362fa25629b938943e/download',
  'https://data.kitware.com/api/v1/item/6086c6362fa25629b9389436/download',
  'https://data.kitware.com/api/v1/item/6086c6362fa25629b938942e/download',
  'https://data.kitware.com/api/v1/item/6086c6352fa25629b9389426/download',
];

export default defineComponent({
  components: {
    ShapeViewer,
  },
  setup() {
    const rows = 3
    const columns = 5
    const glyphSize = 1.5


    const shapeData= ref<ShapeData[]>([])
    onMounted(async () => {
      const shapes = await Promise.all(SHAPE_URLS.map(shapeReader));
      const points = await Promise.all(POINTS_URLS.map(pointsReader));

      shapeData.value = [];
      for (let i = 0; i < 15; i += 1) {
        shapeData.value.push({
          points: points[i],
          shape: shapes[i],
        });
      }
    });

    return {
      rows,
      columns,
      shapeData,
      glyphSize,
    };
  },
});
</script>

<template>
  <shape-viewer
    :data="shapeData"
    :rows="rows"
    :columns="columns"
    :glyph-size="glyphSize"
  />
</template>

<style>
html {
  height: 100vh;
  overflow-y: hidden !important;
}
</style>
