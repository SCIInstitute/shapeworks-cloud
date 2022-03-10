<template>
  <div
    ref="vtk"
    v-resize="resize"
  />
</template>

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

import { AttributeTypes } from 'vtk.js/Sources/Common/DataModel/DataSetAttributes/Constants';
import { ColorMode } from 'vtk.js/Sources/Rendering/Core/Mapper/Constants';
import { FieldDataTypes } from 'vtk.js/Sources/Common/DataModel/DataSet/Constants';

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
    return {};
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
    const renderer = vtkRenderer.newInstance();
    renderWindow.addRenderer(renderer);
    const interactor = vtkRenderWindowInteractor.newInstance();

    const openglRenderWindow = vtkOpenGLRenderWindow.newInstance();
    renderWindow.addView(openglRenderWindow);

    interactor.setView(openglRenderWindow);
    interactor.initialize();
    interactor.setInteractorStyle(vtkInteractorStyleTrackballCamera.newInstance());

    const camera = vtkCamera.newInstance();

    this.vtk = {
      camera,
      renderWindow,
      renderer,
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
    this.vtk.renderer.resetCamera();
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
    addShapes(renderer, shapes) {
      const mapper = vtkMapper.newInstance({
        colorMode: ColorMode.MAP_SCALARS,
      });

      shapes.forEach(
        (shape) => {
          const actor = vtkActor.newInstance();
          actor.getProperty().setColor(1, 1, 1);
          actor.getProperty().setOpacity(1);
          actor.setMapper(mapper);
          if (shape.getClassName() == 'vtkPolyData'){
            mapper.setInputData(shape);
          } else {
            const marchingCube = vtkImageMarchingCubes.newInstance({
              contourValue: 0.0,
              computeNormals: true,
              mergePoints: true,
            });
            marchingCube.setInputData(shape)
            mapper.setInputConnection(marchingCube.getOutputPort());
            marchingCube.setContourValue(0.0001);
          }
          renderer.addActor(actor);
        }
      )
    },
    populateRenderer(renderer, label, shapes) {
      console.log(label)

      this.addShapes(renderer, shapes.map(({shape}) => shape));
    },
    renderGrid() {
      for (let i = 0; i < this.vtk.renderers.length; i += 1) {
        this.vtk.renderWindow.removeRenderer(this.vtk.renderers[i]);
      }
      this.vtk.renderers = [];
      this.vtk.pointMappers = [];

      const data = Object.entries(this.data)
      for (let i = 0; i < this.grid.length; i += 1) {
        let newRenderer = vtkRenderer.newInstance({ background: [0.07, 0.07, 0.07] });
        if(i < data.length){
          this.populateRenderer(newRenderer, data[i][0], data[i][1])
        }
        newRenderer.setViewport.apply(newRenderer, this.grid[i]);
        newRenderer.setActiveCamera(this.vtk.camera);
        newRenderer.resetCamera();
        this.vtk.renderers.push(newRenderer);
        this.vtk.renderWindow.addRenderer(newRenderer);
      }
      this.render();
    },
    render() {
      this.vtk.renderWindow.render();
    },
  },
};
</script>
