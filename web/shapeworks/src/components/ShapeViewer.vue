<template>
  <div
    class="full-screen"
    ref="vtk"
    v-resize="resize"
  />
</template>

<script>
// import vtkActor from 'vtk.js/Sources/Rendering/Core/Actor';
// import vtkColorTransferFunction from 'vtk.js/Sources/Rendering/Core/ColorTransferFunction';
// import vtkGlyph3DMapper from 'vtk.js/Sources/Rendering/Core/Glyph3DMapper';
import vtkInteractorStyleTrackballCamera from 'vtk.js/Sources/Interaction/Style/InteractorStyleTrackballCamera';
// import vtkLookupTable from 'vtk.js/Sources/Common/Core/LookupTable';
// import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
// import vtkOpenGLHardwareSelector from 'vtk.js/Sources/Rendering/OpenGL/HardwareSelector';
import vtkOpenGLRenderWindow from 'vtk.js/Sources/Rendering/OpenGL/RenderWindow';
// import vtkPiecewiseFunction from 'vtk.js/Sources/Common/DataModel/PiecewiseFunction';
import vtkRenderWindow from 'vtk.js/Sources/Rendering/Core/RenderWindow';
import vtkRenderWindowInteractor from 'vtk.js/Sources/Rendering/Core/RenderWindowInteractor';
import vtkRenderer from 'vtk.js/Sources/Rendering/Core/Renderer';
// import vtkSphereSource from 'vtk.js/Sources/Filters/Sources/SphereSource';
// import { FieldAssociations } from 'vtk.js/Sources/Common/DataModel/DataSet/Constants';
/*
import {
  ColorMode,
  ScalarMode,
} from 'vtk.js/Sources/Rendering/Core/Mapper/Constants';
*/


export default {
  props: {
    shape: {
      type: Object,
      required: true,
    },
    points: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {};
  },
  created() {
    this.vtk = {};
    const renderWindow = vtkRenderWindow.newInstance();
    const renderer = vtkRenderer.newInstance();
    renderWindow.addRenderer(renderer);
    const interactor = vtkRenderWindowInteractor.newInstance();

    const openglRenderWindow = vtkOpenGLRenderWindow.newInstance();
    renderWindow.addView(openglRenderWindow);

    interactor.setView(openglRenderWindow);
    interactor.initialize();
    interactor.setInteractorStyle(vtkInteractorStyleTrackballCamera.newInstance());

    this.vtk = {
      renderWindow,
      renderer,
      interactor,
      openglRenderWindow,
    };
    window.vtk = this.vtk;
  },
  mounted() {
    const el = this.$refs.vtk;
    this.vtk.openglRenderWindow.setContainer(el);
    this.vtk.interactor.bindEvents(el);

    this.updateSize();
    this.vtk.renderer.resetCamera();
    this.vtk.renderWindow.render();
  },
  methods: {
    async resize() {
      await this.$nextTick();
      if (this.vtk.renderWindow) {
        this.updateSize();
      }
    },
    updateSize() {
      const el = this.$refs.vtk;
      if (el) {
        const { width, height } = el.getBoundingClientRect();
        this.vtk.openglRenderWindow.setSize(width, height);
      }
    },
  },
};
</script>

<style scoped>
.full-screen {
  height: calc(100vh - 64px);
}
</style>
