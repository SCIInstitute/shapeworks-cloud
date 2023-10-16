import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
import vtkRenderer from 'vtk.js/Sources/Rendering/Core/Renderer';
import vtkSphereSource from 'vtk.js/Sources/Filters/Sources/SphereSource';
import vtkPickerManipulator from 'vtk.js/Sources/Widgets/Manipulators/PickerManipulator';
import vtkSeedWidget from 'vtk.js/Sources/Widgets/Widgets3D/SeedWidget';
import vtkWidgetManager from 'vtk.js/Sources/Widgets/Core/WidgetManager';
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

import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import {
    selectedProject,
    layers, layersShown, orientationIndicator,
    cachedMarchingCubes, cachedParticleComparisonColors, vtkShapesByType,
    analysisFilesShown, currentAnalysisParticlesFiles, meanAnalysisParticlesFiles,
    showDifferenceFromMeanMode, cachedParticleComparisonVectors,
    landmarkInfo, landmarkWidgets, landmarkSize,
    currentLandmarkPlacement, allSetLandmarks,
    cacheComparison, calculateComparisons,
    showGoodBadParticlesMode, goodBadMaxAngle, goodBadAngles,
} from '@/store';
import { SPHERE_RESOLUTION } from '@/store/constants';

export const GOOD_BAD_COLORS = [
    [0, 255, 0],
    [255, 0, 0],
];

export default {
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
        this.vtk.renderers.forEach((renderer, index) => {
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

        if (this.vtk.renderers.indexOf(renderer) >= 0) {
            const targetRendererID = `renderer_${this.vtk.renderers.indexOf(renderer)}`
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
        const rendererID = `renderer_${this.vtk.renderers.indexOf(renderer)}`
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
            camera.setClippingRange(0.1, 1000)
        }
    },
    syncCameras(animation) {
        const targetRenderer = animation.pokedRenderer;
        const { positionDelta, viewUpDelta } = this.getCameraDelta(targetRenderer)

        this.vtk.renderers.filter(
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
                    let c;

                    if (goodBad && analysisFilesShown.value?.length) {
                        if (goodBadAngles.value[domainIndex][i] < goodBadMaxAngle.value) {
                            c = GOOD_BAD_COLORS[0] // green
                        } else {
                            c = GOOD_BAD_COLORS[1] // red
                        }
                    }
                    color[3 * i] = c[0];
                    color[3 * i + 1] = c[1];
                    color[3 * i + 2] = c[2];
                }
                input.forEach((x) => x.modified());
            },
        });
        return filter;
    },
    addLandmarks(label, renderer, points) {
        this.widgetManager = vtkWidgetManager.newInstance();
        this.widgetManager.setRenderer(renderer);

        const actors = renderer.getActors();
        if (actors.length > 0) {
            actors.forEach((actor, actorIndex) => {
                const manipulator = vtkPickerManipulator.newInstance();
                manipulator.getPicker().addPickList(actor);

                const landmarkCoordsData = points?.getPoints().getData()
                landmarkInfo.value.forEach((lInfo, index) => {
                    let widgetId = `${label}_${actorIndex}_${lInfo.id}`
                    let widget = undefined;
                    let handle = undefined;
                    if (landmarkWidgets.value[widgetId]) {
                        widget = landmarkWidgets.value[widgetId]
                    } else {
                        widget = vtkSeedWidget.newInstance();
                        widget.setManipulator(manipulator);
                        landmarkWidgets.value[widgetId] = widget;
                    }

                    this.widgetManager.addWidget(widget).setScaleInPixels(false);
                    handle = widget.getWidgetState().getMoveHandle();
                    handle.setColor3(...lInfo.color);

                    if (currentLandmarkPlacement.value === widgetId) {
                        widget.placeWidget(actor.getBounds());
                        this.widgetManager.grabFocus(widget);
                        this.widgetManager.onModified(() => {
                            const landmarkCoord = widget.getWidgetState().getMoveHandle().getOrigin()
                            if (label && actorIndex >= 0 && currentLandmarkPlacement.value && landmarkCoord) {
                                this.widgetManager.releaseFocus(widget)
                                currentLandmarkPlacement.value = undefined;

                                const shapeKey = `${label}_${actorIndex}`;
                                if (allSetLandmarks.value[shapeKey]) {
                                    allSetLandmarks.value[shapeKey].push(landmarkCoord)
                                } else {
                                    allSetLandmarks.value[shapeKey] = [landmarkCoord]
                                }
                                // reassign store var for listeners
                                allSetLandmarks.value = Object.assign({}, allSetLandmarks.value)
                            }
                        })
                    }

                    handle.setScale1(1 * landmarkSize.value);

                    if (landmarkCoordsData && landmarkCoordsData.length >= index * 3 + 3) {
                        const coords = landmarkCoordsData.slice(index * 3, index * 3 + 3)
                        handle.setOrigin(coords);
                    }
                })
            })
        }
    },
    addPoints(label, renderer, points, i, landmarks = false) {
        let size = this.glyphSize
        let source = vtkSphereSource.newInstance({
            thetaResolution: SPHERE_RESOLUTION,
            phiResolution: SPHERE_RESOLUTION,
        });
        if (landmarks) {
            this.addLandmarks(label, renderer, points)
            return;
        }
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
    addShapes(renderer, label, shapes) {
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
                        const actor = vtkActor.newInstance();
                        actor.getProperty().setColor(...type.rgb);
                        actor.getProperty().setOpacity(opacity);
                        actor.setMapper(mapper);
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
                        renderer.addActor(actor);
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

        this.prepareColorScale()

        this.render()
    },
    prepareColorScale() {
        if (showDifferenceFromMeanMode.value) {
            const canvas = this.$refs.colors
            const labelDiv = this.$refs.colorLabels;
            if (canvas && labelDiv) {
                const { width, height } = canvas
                const context = canvas.getContext('2d', { willReadFrequently: true });
                const pixelsArea = context.getImageData(0, 0, width, height);
                const colorsData = this.lookupTable.getUint8Table(
                    0, 1, height * width, true
                )

                pixelsArea.data.set(colorsData)
                context.putImageData(pixelsArea, 0, 0)
            }

            const labels = [0, 0.25, 0.5, 0.75, 1];
            if (!labelDiv.children.length) {
                labels.forEach((l) => {
                    const child = document.createElement('span');
                    child.innerHTML = (l - 0.5) * 10;
                    labelDiv.appendChild(child);
                })
            }
        }
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

        this.addShapes(renderer, label, shapes.map(({ shape }) => shape));
        shapes.map(({ points }) => points).forEach((pointSet, i) => {
            if (pointSet.getNumberOfPoints() > 0) {
                this.addPoints(label, renderer, pointSet, i);
            }
        })
        shapes.map(({ landmarks }) => landmarks).forEach((landmarkSet, i) => {
            if (landmarkSet && landmarkSet.getNumberOfPoints() > 0) {
                this.addPoints(label, renderer, landmarkSet, i, true);
            }
        })

        const camera = vtkCamera.newInstance();
        renderer.setActiveCamera(camera);
        renderer.resetCamera();
    },
    renderGrid() {
        this.prepareLabelCanvas();

        let { positionDelta, viewUpDelta } = this.getCameraDelta(this.vtk.renderers[0])

        for (let i = 0; i < this.vtk.renderers.length; i += 1) {
            this.vtk.renderWindow.removeRenderer(this.vtk.renderers[i]);
        }
        if (this.vtk.orientationCube) this.vtk.orientationCube.setEnabled(false)
        this.vtk.renderers = [];
        this.vtk.pointMappers = [];

        const data = Object.entries(this.data)
        for (let i = 0; i < this.grid.length; i += 1) {
            let newRenderer = vtkRenderer.newInstance({ background: [0.115, 0.115, 0.115] });
            newRenderer.setViewport.apply(newRenderer, this.grid[i]);
            this.vtk.renderers.push(newRenderer);
            this.vtk.renderWindow.addRenderer(newRenderer);
            if (i < data.length) {
                this.populateRenderer(newRenderer, data[i][0], this.grid[i], data[i][1])
            }
        }
        this.initializeCameras()

        this.vtk.renderers.forEach((renderer, i) => {
            if (positionDelta && viewUpDelta) {
                this.applyCameraDelta(renderer, positionDelta, viewUpDelta)
            }
            if (
                data[i] &&
                (currentLandmarkPlacement.value ||
                    selectedProject.value.landmarks.some(
                        ({ newAddition }) => newAddition
                    )
                )
            ) {
                let label = data[i][0]
                this.addLandmarks(label, renderer, undefined)
            }
        })
        const targetRenderer = this.vtk.renderers[this.columns - 1]
        this.vtk.orientationCube = this.newOrientationCube(this.vtk.interactor)
        if (targetRenderer) {
            this.vtk.orientationCube.setParentRenderer(targetRenderer)
            this.vtk.orientationCube.setEnabled(true);

            this.render();
        }
    },
    render() {
        this.vtk.renderWindow.render();
    },
}
