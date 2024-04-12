<template>
  <div
    ref="vtk"
    v-resize="resize"
    class="render-area"
  >
    <canvas class="labels-canvas" ref="labels"/>
    <div class="color-scales" ref="colors" v-if="showColorScale" />
    <div class ="color-scale-title" ref="colorsTitle" v-if="showColorScale" />
    <div class="color-scale-labels" ref="colorsLabels" v-if="showColorScale" />
  </div>
</template>

<style scoped>
.render-area {
  position: relative;
  height: 100%;
  width: 100%;
}
.labels-canvas {
  position: absolute;
  width: 100%;
  height: 100%;
}
.color-scales {
  position: absolute;
  width: 100%;
  height: 100%;
}
.color-scale-title {
  position: absolute;
  writing-mode: vertical-rl;
  right: -10px;
  text-align: center;
  height: 100%;
}
.color-scale-labels {
  position: absolute;
  width: 100%;
  height: 100%;
}
</style>

<script src="./scripting.js" />
