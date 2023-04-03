<template>
  <div
    ref="vtk"
    v-resize="resize"
    class="render-area"
  >
    <canvas class="labels-canvas" ref="labels"/>
    <canvas class="color-scale-canvas" ref="colors" v-if="showDifferenceFromMeanMode"/>
    <div class ="color-scale-title-text" v-if="showDifferenceFromMeanMode">Distance from particle on mean shape</div>
    <div class="color-scale-labels-canvas" ref="colorLabels" v-if="showDifferenceFromMeanMode"/>
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
.color-scale-canvas {
  position: absolute;
  right: 10px;
  width: 20px;
  height: 100%;
  z-index: 1;
}
.color-scale-labels-canvas {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
  position: absolute;
  right: 35px;
  width: 50px;
  height: 100%;
}
.color-scale-title-text {
  position: absolute;
  writing-mode: vertical-rl;
  right: -10px;
  text-align: center;;
  height: 100%;
}
</style>

<script src="./scripting.js" />
