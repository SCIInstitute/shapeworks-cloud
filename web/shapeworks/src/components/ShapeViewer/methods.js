import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkRenderer from 'vtk.js/Sources/Rendering/Core/Renderer';
import vtkSphereSource from 'vtk.js/Sources/Filters/Sources/SphereSource';
import vtkImageMarchingCubes from 'vtk.js/Sources/Filters/General/ImageMarchingCubes';
import vtkOrientationMarkerWidget from 'vtk.js/Sources/Interaction/Widgets/OrientationMarkerWidget';
import vtkArrowSource from 'vtk.js/Sources/Filters/Sources/ArrowSource'
import vtkDataArray from 'vtk.js/Sources/Common/Core/DataArray';
import vtkActor from 'vtk.js/Sources/Rendering/Core/Actor';
import vtkCalculator from 'vtk.js/Sources/Filters/General/Calculator';
import vtkCamera from 'vtk.js/Sources/Rendering/Core/Camera';
import vtkGlyph3DMapper from 'vtk.js/Sources/Rendering/Core/Glyph3DMapper';
import { AttributeTypes } from 'vtk.js/Sources/Common/DataModel/DataSetAttributes/Constants';
import { ColorMode, ScalarMode } from 'vtk.js/Sources/Rendering/Core/Mapper/Constants';
import { FieldDataTypes } from 'vtk.js/Sources/Common/DataModel/DataSet/Constants';

import {
    renderLoading, layers, layersShown, orientationIndicator, imageViewIntersectMode,
    cachedMarchingCubes, cachedParticleComparisonColors, vtkShapesByType,
    analysisFilesShown, currentAnalysisParticlesFiles, meanAnalysisParticlesFiles,
    showDifferenceFromMeanMode, cachedParticleComparisonVectors,
    cacheComparison, calculateComparisons, deepSSMDataTab, uniformScale,
    showGoodBadParticlesMode, goodBadMaxAngle, goodBadAngles, deepSSMErrorGlobalRange,
} from '@/store';
import { SPHERE_RESOLUTION } from '@/store/constants';
import widgetSync from './widgetSync';
import imageSync from './imageSync';

export const GOOD_BAD_COLORS = [
    [0, 255, 0],
    [255, 0, 0],
];
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
    ...widgetSync,
    ...imageSync,
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
    newOrientationCube(interactor) {
        return vtkOrientationMarkerWidget.newInstance({
            actor: orientationIndicator.value,
            interactor: interactor,
            viewportSize: 0.1,
            minPixelSize: 100,
            maxPixelSize: 300,
            viewportCorner: vtkOrientationMarkerWidget.Corners.TOP_RIGHT,
        });
    },
    initializeCameras() {
        this.initialCameraStates = {
            position: {},
            viewUp: {},
        }
        Object.values(this.vtk.renderers).forEach((renderer, index) => {
            const camera = renderer.getActiveCamera();
            this.initialCameraStates.position[`renderer_${index}`] = [...camera.getReferenceByName('position')]
            this.initialCameraStates.viewUp[`renderer_${index}`] = [...camera.getReferenceByName('viewUp')]
        })
    },
    getCameraDelta(renderer) {
        if (!renderer) return {
            positionDelta: undefined,
            viewUpDelta: undefined,
        }
        const targetCamera = renderer.getActiveCamera();
        const rendererIndex = Object.values(this.vtk.renderers).indexOf(renderer)

        if (rendererIndex >= 0) {
            const targetRendererID = `renderer_${rendererIndex}`
            this.initialCameraPosition = this.initialCameraStates.position[targetRendererID]
            this.initialCameraViewUp = this.initialCameraStates.viewUp[targetRendererID]
            this.newCameraPosition = targetCamera.getReferenceByName('position')
            this.newCameraViewUp = targetCamera.getReferenceByName('viewUp')
        }
        const positionDelta = [...this.newCameraPosition].map(
            (num, index) => num - this.initialCameraPosition[index]
        )
        const viewUpDelta = [...this.newCameraViewUp].map(
            (num, index) => num - this.initialCameraViewUp[index]
        )
        return {
            positionDelta,
            viewUpDelta,
        }
    },
    applyCameraDelta(renderer, positionDelta, viewUpDelta) {
        const camera = renderer.getActiveCamera();
        const rendererIndex = Object.values(this.vtk.renderers).indexOf(renderer)
        const rendererID = `renderer_${rendererIndex}`
        if (this.initialCameraStates.position[rendererID]) {
            camera.setPosition(
                ...this.initialCameraStates.position[rendererID].map(
                    (old, index) => old + positionDelta[index]
                )
            )
            camera.setViewUp(
                ...this.initialCameraStates.viewUp[rendererID].map(
                    (old, index) => old + viewUpDelta[index]
                )
            )
        }
        renderer.resetCameraClippingRange()
    },
    syncCameras(animation) {
        const targetRenderer = animation.pokedRenderer;
        const { positionDelta, viewUpDelta } = this.getCameraDelta(targetRenderer)

        Object.values(this.vtk.renderers).filter(
            (renderer) => renderer !== targetRenderer
        ).forEach((renderer) => {
            this.applyCameraDelta(renderer, positionDelta, viewUpDelta)
        })
    },
    createColorFilter(domainIndex = 0, goodBad = false) {
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
                    let c = COLORS[i % COLORS.length];

                    if (goodBad && analysisFilesShown.value?.length) {
                        if (goodBadAngles.value[domainIndex][i] < goodBadMaxAngle.value) {
                            c = GOOD_BAD_COLORS[0] // green
                        } else {
                            c = GOOD_BAD_COLORS[1] // red
                        }
                    }
                    if (c) {
                        color[3 * i] = c[0];
                        color[3 * i + 1] = c[1];
                        color[3 * i + 2] = c[2];
                    }
                }
                input.forEach((x) => x.modified());
            },
        });
        return filter;
    },
    addPoints(renderer, points, i) {
        let size = this.glyphSize
        let source = vtkSphereSource.newInstance({
            thetaResolution: SPHERE_RESOLUTION,
            phiResolution: SPHERE_RESOLUTION,
        });
        const mapper = vtkGlyph3DMapper.newInstance({
            scaleMode: vtkGlyph3DMapper.SCALE_BY_CONSTANT,
            scaleFactor: size,
        });
        const actor = vtkActor.newInstance();
        const filter = this.createColorFilter(i, showGoodBadParticlesMode.value);

        filter.setInputData(points, 0);
        mapper.setInputConnection(filter.getOutputPort(), 0);
        mapper.setInputConnection(source.getOutputPort(), 1);
        actor.setMapper(mapper);

        renderer.addActor(actor);
        this.vtk.pointMappers.push(mapper);
    },
    addShapes(renderer, shapes) {
        let label;
        Object.entries(this.vtk.renderers).forEach(([l, r]) => {
            if (renderer == r) label = l
        })
        shapes.forEach(
            (shapeDatas, domainIndex) => {
                shapeDatas.forEach(
                    (shapeData) => {
                        let layerName = Object.entries(vtkShapesByType.value).filter(
                            ([, shapes]) => shapes.includes(shapeData)
                        ).map(
                            ([layerName,]) => layerName
                        )
                        layerName = layerName.length ? layerName[0] : "Original"
                        const type = layers.value.find((layer) => layer.name === layerName)
                        let opacity = 1;
                        if (!analysisFilesShown.value?.length) {
                            const numLayers = layersShown.value.filter(
                                (layerName) => layers.value.find((layer) => layer.name == layerName).rgb
                            ).length
                            if (numLayers > 0) opacity /= numLayers
                        }
                        const cacheLabel = `${label}_${layerName}_${domainIndex}`

                        const mapper = vtkMapper.newInstance({
                            colorMode: ColorMode.MAP_SCALARS,
                            scalarMode: ScalarMode.USE_POINT_FIELD_DATA,
                        });
                        if (shapeData.getClassName() == 'vtkImageData' && layerName === 'Original - Image') {
                            this.addImage(shapeData, renderer)
                        } else {
                            if (shapeData.getClassName() == 'vtkPolyData') {
                                mapper.setInputData(shapeData);
                            } else if (cachedMarchingCubes.value[cacheLabel]) {
                                mapper.setInputData(cachedMarchingCubes.value[cacheLabel])
                            } else {
                                const marchingCube = vtkImageMarchingCubes.newInstance({
                                    contourValue: 0.001,
                                    computeNormals: true,
                                    mergePoints: true,
                                });
                                marchingCube.setInputData(shapeData)
                                mapper.setInputConnection(marchingCube.getOutputPort());
                                cachedMarchingCubes.value[cacheLabel] = marchingCube.getOutputData()
                            }
                            if (showDifferenceFromMeanMode.value) {
                                this.showDifferenceFromMean(mapper, renderer, label, domainIndex)
                            }
                            if ([1, 2].includes(deepSSMDataTab.value)) {
                                let data;
                                if (shapeData.getPointData().getArrayByName('deepssm_error')) {
                                    data = shapeData.getPointData().getArrayByName('deepssm_error').getData()
                                }

                                if (data) {
                                    let normalizeRange;
                                    if (uniformScale.value) {
                                        normalizeRange = deepSSMErrorGlobalRange.value
                                    } else {
                                        normalizeRange = [Math.min(...data), Math.max(...data)]
                                    }
                                    const normalizedData = data.map((v) => v / (normalizeRange[1] - normalizeRange[0]))
                                    const normalizedArray = vtkDataArray.newInstance({
                                        name: 'deepssm_error_normalized',
                                        values: normalizedData,
                                    })
                                    shapeData.getPointData().addArray(normalizedArray)
                                    mapper.setColorByArrayName('deepssm_error_normalized')
                                    mapper.setLookupTable(this.lookupTable)
                                }
                            }
                            const actor = vtkActor.newInstance();
                            if (type) actor.getProperty().setColor(...type.rgb);
                            actor.getProperty().setOpacity(opacity);
                            actor.setMapper(mapper);
                            renderer.addActor(actor);
                        }
                    }
                )
            }
        )
    },
    showDifferenceFromMean(mapper, renderer, label, index) {
        if (!analysisFilesShown.value
            || !currentAnalysisParticlesFiles.value
            || !meanAnalysisParticlesFiles.value
            || !this.metaData[label]
            || !this.metaData[label][index]) return

        // color values should be between 0 and 1
        // 0.5 is green, representing no difference between particles
        const targetMetaData = this.metaData[label][index]
        const currentPoints = targetMetaData.current.points.getPoints().getData()
        const meanPoints = targetMetaData.mean.points.getPoints().getData()

        const particleComparisonKey = currentAnalysisParticlesFiles.value[index]
        let colorValues;
        let vectorValues;
        if (
            particleComparisonKey in cachedParticleComparisonColors.value
            && particleComparisonKey in cachedParticleComparisonVectors.value
        ) {
            colorValues = cachedParticleComparisonColors.value[particleComparisonKey]
            vectorValues = cachedParticleComparisonVectors.value[particleComparisonKey]
        } else {
            const comparisons = calculateComparisons(mapper, currentPoints, meanPoints);
            colorValues = comparisons.colorValues;
            vectorValues = comparisons.vectorValues;

            cacheComparison(colorValues, vectorValues, particleComparisonKey);
        }

        if (vectorValues) {
            const vectorMapper = vtkGlyph3DMapper.newInstance({
                colorMode: ColorMode.MAP_SCALARS,
                scalarMode: ScalarMode.USE_POINT_FIELD_DATA,
            })
            const vectorActor = vtkActor.newInstance()
            const vectorSource = vtkPolyData.newInstance()
            const vectorShape = vtkArrowSource.newInstance();

            const verts = new Uint32Array(vectorValues.length + 1)
            verts[0] = vectorValues.length
            for (let i = 0; i < vectorValues.length; i++) {
                verts[i + 1] = i
            }
            let locations = []
            let orientations = []
            let colors = []

            for (let i = 0; i < vectorValues.length; i++) {
                const [x, y, z, d, dx, dy, dz] = vectorValues[i]
                if (d < 0) {
                    const shift = 3  // based on arrow size
                    locations.push([x + dx * shift, y + dy * shift, z + dz * shift])
                    orientations.push([-dx, -dy, -dz])
                    colors.push(d / 10 + 0.5)
                } else if (d > 0) {
                    locations.push([x + dx, y + dy, z + dz])
                    orientations.push([dx, dy, dz])
                    colors.push(d / 10 + 0.5)
                }
            }

            vectorSource.getPointData().addArray(
                vtkDataArray.newInstance({
                    name: 'color',
                    values: colors
                })
            )
            vectorSource.getPointData().addArray(
                vtkDataArray.newInstance({
                    name: 'normal',
                    values: orientations.flat(),
                    numberOfComponents: 3
                })
            )
            vectorSource.getPoints().setData(locations.flat(), 3)
            vectorSource.getVerts().setData(verts);
            vectorActor.setMapper(vectorMapper)
            vectorMapper.setInputData(vectorSource)
            vectorMapper.addInputConnection(vectorShape.getOutputPort(), 1)
            vectorMapper.setScaleFactor(5)
            vectorMapper.setColorByArrayName('color')
            vectorMapper.setOrientationArray('normal')
            vectorMapper.setLookupTable(this.lookupTable)
            renderer.addActor(vectorActor)
        }

        const colorArray = vtkDataArray.newInstance({
            name: 'color',
            values: colorValues
        })
        mapper.getInputData().getPointData().addArray(colorArray)
        mapper.getInputData().modified()
        mapper.setLookupTable(this.lookupTable)
        mapper.setColorByArrayName('color')

        if (showDifferenceFromMeanMode.value) {
            this.lookupTable.setMappingRange(0, 1)
            this.lookupTable.updateRange();
            this.prepareColorScales()
        }

        this.render()
    },
    prepareColorScales() {
        const canvasDiv = this.$refs.colors
        const titleDiv = this.$refs.colorsTitle
        const labelsDiv = this.$refs.colorsLabels
        canvasDiv.innerHTML = ""
        titleDiv.innerHTML = ""
        labelsDiv.innerHTML = ""
        if (showDifferenceFromMeanMode.value || uniformScale.value) {
            const canvas = document.createElement('canvas')
            canvas.style.right = "10px"
            canvas.style.height = "100%"
            canvas.style.width = "20px"
            canvasDiv.appendChild(canvas)

            const labels = document.createElement('div')
            labels.style.right = "35px"
            labels.style.height = "100%"
            labelsDiv.appendChild(labels)

            let range = [-5, 5]
            if (showDifferenceFromMeanMode.value) {
                titleDiv.innerHTML = "Distance from particle on mean shape"
            } else if (uniformScale.value) {
                titleDiv.innerHTML = "DeepSSMError"
                range = deepSSMErrorGlobalRange.value
            }
            this.prepareColorScale(canvas, labels, range)
        } else {
            Object.entries(this.data).forEach(([, data], i) => {
                // if the shape (vtk only) doesn't have the deepssm_error array, don't show the color scale
                if (data[0].shape.filter((shape) => shape.getClassName() === 'vtkPolyData' && !shape.getPointData().getArrayByName('deepssm_error')).length > 0) {
                    return;
                }
                const [, y1, x2, y2] = this.grid[i]
                const canvas = document.createElement('canvas')
                canvas.style.top = `calc(${(1 - y2) * 100}%)`
                canvas.style.right = `calc(${(1 - x2) * 100}% + 10px)`
                canvas.style.height = `${(y2 - y1) * 96}%`
                canvas.style.width = "10px"
                canvasDiv.appendChild(canvas)

                const labels = document.createElement('div')
                labels.style.top = `calc(${(1 - y2) * 100}%)`
                labels.style.right = `calc(${(1 - x2) * 100}% + 35px)`
                labels.style.height = `${(y2 - y1) * 96}%`
                labelsDiv.appendChild(labels)

                let range = [-5, 5]
                data[0].shape.forEach((shape) => {
                    if (shape.getClassName() === 'vtkPolyData') {
                        const arr = shape.getPointData().getArrayByName('deepssm_error').getData()
                        if (arr) range = [Math.min(...arr), Math.max(...arr)]
                    }
                })
                this.prepareColorScale(canvas, labels, range)
            })
        }
    },
    prepareColorScale(canvas, labels, range) {
        if (canvas && labels) {
            canvas.style.position = "absolute"
            canvas.style.zIndex = "1"
            const { width, height } = canvas
            const context = canvas.getContext('2d', { willReadFrequently: true });
            const pixelsArea = context.getImageData(0, 0, width, height);
            const colorsData = this.lookupTable.getUint8Table(
                ...this.lookupTable.getMappingRange(),
                height * width,
                true
            )
            pixelsArea.data.set(colorsData)
            context.putImageData(pixelsArea, 0, 0)

            const labelProportions = [1, 0.75, 0.5, 0.25, 0];
            labels.innerHTML = ''
            labels.style.position = "absolute"
            labels.style.display = "flex"
            labels.style.flexDirection = "column"
            labels.style.justifyContent = "space-between"
            labels.style.alignItems = "flex-end"
            labels.style.textAlign = "right"
            labelProportions.forEach((p) => {
                const child = document.createElement('span');
                child.innerHTML = Math.round(p * (range[1] - range[0]) + range[0]);
                labels.appendChild(child);
            })
        }
    },
    prepareLabelCanvas() {
        const labelCanvas = this.$refs.labels
        const labelCanvasContext = labelCanvas.getContext('2d')
        const { clientWidth, clientHeight } = this.$refs.vtk;
        // increase the resolution of the canvas so text isn't blurry
        labelCanvas.width = clientWidth;
        labelCanvas.height = clientHeight;

        labelCanvasContext.clearRect(0, 0, labelCanvas.width, labelCanvas.height)
        labelCanvasContext.font = "16px Arial";
        labelCanvasContext.fillStyle = "white";
    },
    populateRenderer(renderer, shapes) {
        this.addShapes(renderer, shapes.map(({ shape }) => shape));
        shapes.map(({ points }) => points).forEach((pointSet, i) => {
            if (pointSet.getNumberOfPoints() > 0) {
                this.addPoints(renderer, pointSet, i);
            }
        })

        const camera = vtkCamera.newInstance();
        renderer.setActiveCamera(camera);
        renderer.resetCamera();
    },
    renderGrid() {
        this.vtk.interactor.disable()
        Object.values(this.vtk.widgetManagers).forEach((wm) => {
            wm.disablePicking()
        })

        this.resetImageSlices()
        this.prepareLabelCanvas();
        let positionDelta, viewUpDelta

        const renderers = Object.values(this.vtk.renderers)
        for (let i = 0; i < renderers.length; i += 1) {
            if (!positionDelta || !viewUpDelta) {
                ({ positionDelta, viewUpDelta } = this.getCameraDelta(Object.values(this.vtk.renderers)[0]))
            }
            this.vtk.renderWindow.removeRenderer(renderers[i]);
        }
        if (this.vtk.orientationCube) this.vtk.orientationCube.setEnabled(false)
        this.vtk.renderers = {};
        this.vtk.pointMappers = [];

        const data = Object.entries(this.data)
        for (let i = 0; i < data.length; i += 1) {
            const [label, shapes] = data[i];
            const newRenderer = vtkRenderer.newInstance({ background: [0.115, 0.115, 0.115] });
            const bounds = this.grid[i];

            const labelCanvas = this.$refs.labels
            const labelCanvasContext = labelCanvas.getContext('2d')
            labelCanvasContext.fillText(
                label,
                labelCanvas.width * bounds[0],
                labelCanvas.height * (1 - bounds[1]) - 20
            );
            newRenderer.setViewport.apply(newRenderer, bounds);
            this.vtk.renderers[label] = newRenderer;
            this.vtk.renderWindow.addRenderer(newRenderer);
            if (i < data.length) {
                this.populateRenderer(newRenderer, shapes)
            }
        }
        this.initializeCameras()
        this.initializeWidgets()

        if (positionDelta && viewUpDelta) {
            Object.values(this.vtk.renderers).forEach((renderer) => {
                this.applyCameraDelta(renderer, positionDelta, viewUpDelta)
            })
        }

        // layers shown may have changed intersections
        // this should be done after all layers are added
        if (imageViewIntersectMode.value) this.resetIntersections()

        else if ([1, 2].includes(deepSSMDataTab.value)) {
            this.prepareColorScales()
        }

        if (!this.showColorScale) {
            const targetRenderer = Object.values(this.vtk.renderers)[this.columns - 1]
            if (targetRenderer) {
                this.vtk.orientationCube.setParentRenderer(targetRenderer)
                this.vtk.orientationCube.setEnabled(true);
            }
        }
        this.vtk.interactor.enable()
        this.render();
        renderLoading.value = false;
        setTimeout(
            () => {
                Object.values(this.vtk.widgetManagers).forEach((wm) => {
                    wm.enablePicking()
                })
            }, 100
        )
    },
    render() {
        this.vtk.renderWindow.render();
    },
}
