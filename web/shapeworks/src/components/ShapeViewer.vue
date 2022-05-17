<template>
  <div
    ref="vtk"
    v-resize="resize"
    style="position: relative;"
  >
  <canvas class="labels-canvas" ref="labels"/>
  </div>
</template>

<style scoped>
.labels-canvas {
  position: absolute;
  width: 100%;
  height: 100%;
}
</style>

<script>
import 'vtk.js/Sources/Rendering/Profiles/All';

import vtkActor from 'vtk.js/Sources/Rendering/Core/Actor';
import vtkCalculator from 'vtk.js/Sources/Filters/General/Calculator';
import vtkCamera from 'vtk.js/Sources/Rendering/Core/Camera';
import vtkGlyph3DMapper from 'vtk.js/Sources/Rendering/Core/Glyph3DMapper';
import vtkInteractorStyleTrackballCamera from 'vtk.js/Sources/Interaction/Style/InteractorStyleTrackballCamera';
import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
import vtkOpenGLRenderWindow from 'vtk.js/Sources/Rendering/OpenGL/RenderWindow';
import vtkRenderWindow from 'vtk.js/Sources/Rendering/Core/RenderWindow';
import vtkRenderWindowInteractor from 'vtk.js/Sources/Rendering/Core/RenderWindowInteractor';
import vtkRenderer from 'vtk.js/Sources/Rendering/Core/Renderer';
import vtkSphereSource from 'vtk.js/Sources/Filters/Sources/SphereSource';
import vtkImageMarchingCubes from 'vtk.js/Sources/Filters/General/ImageMarchingCubes';
import vtkOrientationMarkerWidget from 'vtk.js/Sources/Interaction/Widgets/OrientationMarkerWidget';

import { AttributeTypes } from 'vtk.js/Sources/Common/DataModel/DataSetAttributes/Constants';
import { ColorMode } from 'vtk.js/Sources/Rendering/Core/Mapper/Constants';
import { FieldDataTypes } from 'vtk.js/Sources/Common/DataModel/DataSet/Constants';
import { layers, layersShown, orientationIndicator, cachedMarchingCubes } from '../store';


const SPHERE_RESOLUTION = 32;
const COLORS = [
  [166, 206, 227],
  [31, 120, 180],
  [178, 223, 138],
  [51, 160, 44],
  [251, 154, 153],
  [227, 26, 28],
  [253, 191, 111],
  [255, 127, 0],
  [202, 178, 214],
  [106, 61, 154],
  [255, 255, 153],
  [177, 89, 40],
];

export default {
  props: {
    data: {
      type: Object,
      required: true,
    },
    rows: {
      type: Number,
      required: true,
    },
    columns: {
      type: Number,
      required: true,
    },
    glyphSize: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    grid() {
      const grid = [];
      const nx = this.columns;
      const ny = this.rows;
      for (let y = 0; y < ny; y += 1) {
        for (let x = 0; x < nx; x += 1) {
          const xmin = x / nx;
          const ymin = y / ny;
          const xmax = (x + 1) / nx;
          const ymax = (y + 1) / ny;
          grid.push([xmin, 1 - ymax, xmax, 1 - ymin]);
        }
      }
      return grid;
    },
    labelCanvas() {
      return this.$refs.labels;
    },
    labelCanvasContext() {
      return this.labelCanvas.getContext("2d");
    }
  },
  watch: {
    data() {
      this.renderGrid();
    },
    grid() {
      this.renderGrid();
    },
    glyphSize() {
      this.vtk.pointMappers.forEach((mapper) => {
        mapper.setScaleFactor(this.glyphSize);
      });
      this.render();
    },
  },
  beforeDestroy() {
    this.vtk.interactor.unbindEvents();
    this.vtk.openglRenderWindow.delete();
  },
  created() {
    const renderWindow = vtkRenderWindow.newInstance();
    const openglRenderWindow = vtkOpenGLRenderWindow.newInstance();
    renderWindow.addView(openglRenderWindow);

    const interactor = vtkRenderWindowInteractor.newInstance();
    interactor.setView(openglRenderWindow);
    interactor.initialize();
    interactor.setInteractorStyle(vtkInteractorStyleTrackballCamera.newInstance());
    interactor.onAnimation(this.syncCameras)

    this.vtk = {
      renderWindow,
      interactor,
      openglRenderWindow,
      renderers: [],
      pointMappers: [],
    };
  },
  mounted() {
    const el = this.$refs.vtk;
    this.vtk.openglRenderWindow.setContainer(el);
    this.vtk.interactor.bindEvents(el);

    this.updateSize();
    this.renderGrid();
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
        this.render();
      }
    },
    syncCameras(animation) {
      const targetRenderer = animation.pokedRenderer;
      const targetCamera = targetRenderer.getActiveCamera();
      const newPosition = targetCamera.getReferenceByName('position');
      const newViewUp = targetCamera.getReferenceByName('viewUp');
      const newViewAngle = targetCamera.getReferenceByName('viewAngle');
      const newClippingRange = targetCamera.getClippingRange();
      const otherRenderers = this.vtk.renderers.filter(
        (renderer) => renderer.getActiveCamera() !== targetCamera
      )
      otherRenderers.forEach((renderer) => {
        const camera = renderer.getActiveCamera();
        camera.setPosition(...newPosition)
        camera.setViewUp(...newViewUp)
        camera.setViewAngle(newViewAngle)
        camera.setClippingRange(...newClippingRange)
      })
    },
    createColorFilter() {
      const filter = vtkCalculator.newInstance()
      filter.setFormula({
        getArrays() {
          return {
            input: [{ location: FieldDataTypes.COORDINATE }],
            output: [{
              location: FieldDataTypes.POINT,
              name: 'color',
              dataType: 'Uint8Array',
              attribute: AttributeTypes.SCALARS,
              numberOfComponents: 3,
            }],
          };
        },
        evaluate(input, output) {
          const [coords] = input.map((d) => d.getData());
          const [color] = output.map((d) => d.getData());

          const n = coords.length / 3;
          for (let i = 0; i < n; i += 1) {
            const c = COLORS[i % COLORS.length];
            color[3 * i] = c[0];
            color[3 * i + 1] = c[1];
            color[3 * i + 2] = c[2];
          }
          input.forEach((x) => x.modified());
        },
      });
      return filter;
    },
    addPoints(renderer, points) {
      const source = vtkSphereSource.newInstance({
        thetaResolution: SPHERE_RESOLUTION,
        phiResolution: SPHERE_RESOLUTION,
      });
      const mapper = vtkGlyph3DMapper.newInstance({
        scaleMode: vtkGlyph3DMapper.SCALE_BY_CONSTANT,
        scaleFactor: this.glyphSize,
      });
      const actor = vtkActor.newInstance();
      const filter = this.createColorFilter();

      filter.setInputData(points, 0);
      mapper.setInputConnection(filter.getOutputPort(), 0);
      mapper.setInputConnection(source.getOutputPort(), 1);
      actor.setMapper(mapper);
      renderer.addActor(actor);
      this.vtk.pointMappers.push(mapper);
    },
    addShapes(renderer, label, shapes) {
      shapes.flat().forEach(
        (shape, index) => {
          const layerName = shape.getFieldData().get('type').type
          const type = layers.value.find((layer) => layer.name === layerName)
          let opacity = 1;
          const numLayers = layersShown.value.filter(
            (layerName) => layers.value.find((layer) => layer.name == layerName).rgb
          ).length
          if(numLayers > 0) opacity /= numLayers
          const cacheLabel = `${label}_${layerName}_${index}`

          const mapper = vtkMapper.newInstance({
            colorMode: ColorMode.MAP_SCALARS,
          });
          const actor = vtkActor.newInstance();
          actor.getProperty().setColor(...type.rgb);
          actor.getProperty().setOpacity(opacity);
          actor.setMapper(mapper);
          if (shape.getClassName() == 'vtkPolyData'){
            mapper.setInputData(shape);
          } else if (cachedMarchingCubes.value[cacheLabel]) {
            mapper.setInputData(cachedMarchingCubes.value[cacheLabel])
          } else {
            const marchingCube = vtkImageMarchingCubes.newInstance({
              contourValue: 0.001,
              computeNormals: true,
              mergePoints: true,
            });
            marchingCube.setInputData(shape)
            mapper.setInputConnection(marchingCube.getOutputPort());
            cachedMarchingCubes.value[cacheLabel] = marchingCube.getOutputData()
          }
          renderer.addActor(actor);
        }
      )
    },
    prepareLabelCanvas() {
      const { clientWidth, clientHeight } = this.$refs.vtk;
      // increase the resolution of the canvas so text isn't blurry
      this.labelCanvas.width = clientWidth;
      this.labelCanvas.height = clientHeight;

      this.labelCanvasContext.clearRect(0, 0, this.labelCanvas.width, this.labelCanvas.height)
      this.labelCanvasContext.font = "16px Arial";
      this.labelCanvasContext.fillStyle = "white";
    },
    populateRenderer(renderer, label, bounds, shapes) {
      this.labelCanvasContext.fillText(
        label,
        this.labelCanvas.width * bounds[0],
        this.labelCanvas.height * (1 - bounds[1]) - 20
      );

      this.addShapes(renderer, label, shapes.map(({shape}) => shape));
      const points = shapes.map(({points}) => points)
      if(points.length > 0 && points[0].getNumberOfPoints() > 0) this.addPoints(renderer, points[0]);

      const camera = vtkCamera.newInstance();
      renderer.setActiveCamera(camera);
      renderer.resetCamera();
    },
    renderGrid() {
      this.prepareLabelCanvas();
      for (let i = 0; i < this.vtk.renderers.length; i += 1) {
        this.vtk.renderWindow.removeRenderer(this.vtk.renderers[i]);
      }
      this.vtk.renderers = [];
      this.vtk.pointMappers = [];

      const data = Object.entries(this.data)
      for (let i = 0; i < this.grid.length; i += 1) {
        let newRenderer = vtkRenderer.newInstance({ background: [0.07, 0.07, 0.07] });
        if(i < data.length){
          this.populateRenderer(newRenderer, data[i][0], this.grid[i], data[i][1])
        }
        newRenderer.setViewport.apply(newRenderer, this.grid[i]);
        this.vtk.renderers.push(newRenderer);
        this.vtk.renderWindow.addRenderer(newRenderer);
      }

      const orientationWidget = vtkOrientationMarkerWidget.newInstance({
        actor: orientationIndicator.value,
        interactor: this.vtk.interactor,
      });
      orientationWidget.setEnabled(true);
      orientationWidget.setViewportCorner(
        vtkOrientationMarkerWidget.Corners.TOP_RIGHT
      );
      orientationWidget.setViewportSize(0.10);
      orientationWidget.setMinPixelSize(100);
      orientationWidget.setMaxPixelSize(300);

      this.render();
    },
    render() {
      this.vtk.renderWindow.render();
    },
  },
};
</script>
