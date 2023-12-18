import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkRenderer from 'vtk.js/Sources/Rendering/Core/Renderer';
import vtkSphereSource from 'vtk.js/Sources/Filters/Sources/SphereSource';
import vtkPickerManipulator from 'vtk.js/Sources/Widgets/Manipulators/PickerManipulator';
import vtkWidgetManager from 'vtk.js/Sources/Widgets/Core/WidgetManager';
import vtkImageMarchingCubes from 'vtk.js/Sources/Filters/General/ImageMarchingCubes';
import vtkOrientationMarkerWidget from 'vtk.js/Sources/Interaction/Widgets/OrientationMarkerWidget';
import vtkSeedWidget from 'vtk.js/Sources/Widgets/Widgets3D/SeedWidget';
import vtkPaintWidget from 'vtk.js/Sources/Widgets/Widgets3D/PaintWidget';
import vtkImplicitPlaneWidget from 'vtk.js/Sources/Widgets/Widgets3D/ImplicitPlaneWidget'
import vtkArrowSource from 'vtk.js/Sources/Filters/Sources/ArrowSource'
import vtkDataArray from 'vtk.js/Sources/Common/Core/DataArray';
import vtkColorTransferFunction from 'vtk.js/Sources/Rendering/Core/ColorTransferFunction';
import vtkActor from 'vtk.js/Sources/Rendering/Core/Actor';
import vtkCalculator from 'vtk.js/Sources/Filters/General/Calculator';
import vtkCamera from 'vtk.js/Sources/Rendering/Core/Camera';
import vtkGlyph3DMapper from 'vtk.js/Sources/Rendering/Core/Glyph3DMapper';
import { AttributeTypes } from 'vtk.js/Sources/Common/DataModel/DataSetAttributes/Constants';
import { ColorMode, ScalarMode } from 'vtk.js/Sources/Rendering/Core/Mapper/Constants';
import { FieldDataTypes } from 'vtk.js/Sources/Common/DataModel/DataSet/Constants';

import { kdTree } from 'kd-tree-javascript';
import { distance } from '@/helper'

import {
    layers, layersShown, orientationIndicator,
    cachedMarchingCubes, cachedParticleComparisonColors, vtkShapesByType,
    analysisFilesShown, currentAnalysisParticlesFiles, meanAnalysisParticlesFiles,
    showDifferenceFromMeanMode, cachedParticleComparisonVectors,
    getWidgetInfo, landmarkInfo, landmarkSize, currentLandmarkPlacement,
    getLandmarkLocation, setLandmarkLocation,
    allSetLandmarks, reassignLandmarkNumSetValues,
    constraintInfo, constraintsShown, allSetConstraints, currentConstraintPlacement,
    getConstraintLocation, setConstraintLocation, constraintPaintRadius,
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
    addLandmarks(label, renderer, widgetManager) {
        renderer.getActors().forEach((actor) => {
            const manipulator = vtkPickerManipulator.newInstance();
            manipulator.getPicker().addPickList(actor);
            const mapper = actor.getMapper()
            const inputData = mapper.getInputData()
            const inputDataDomain = inputData.getFieldData().getArrayByName('domain').getData()[0]

            landmarkInfo.value.forEach((lInfo) => {
                if (lInfo.domain === inputDataDomain) {
                    let widget = vtkSeedWidget.newInstance();
                    widget.setManipulator(manipulator);
                    widgetManager.addWidget(widget).setScaleInPixels(false);
                    let handle = widget.getWidgetState().getMoveHandle();

                    // Handle current landmark placement widget
                    if (currentLandmarkPlacement.value === getWidgetInfo({ name: label }, lInfo)) {
                        widget.placeWidget(actor.getBounds());
                        widgetManager.grabFocus(widget);
                        widgetManager.onModified(() => {
                            const landmarkCoord = handle.getOrigin()
                            if (currentLandmarkPlacement.value && landmarkCoord) {
                                widgetManager.releaseFocus(widget)
                                currentLandmarkPlacement.value = undefined;
                            }
                        })
                    }

                    // Set color, scale, and position of widget
                    handle.setColor3(...lInfo.color);
                    handle.setScale1(landmarkSize.value);
                    const location = getLandmarkLocation({ name: label }, lInfo)
                    if (location) handle.setOrigin(location);

                    widget.onWidgetChange(() => {
                        // When widget moved, update value in allSetLandmarks
                        const landmarkCoord = handle.getOrigin()
                        if (landmarkCoord) {
                            widgetManager.releaseFocus(widget);
                            setLandmarkLocation({ name: label }, lInfo, landmarkCoord)
                            // reassign store var for listeners
                            allSetLandmarks.value = Object.assign({}, allSetLandmarks.value)
                            reassignLandmarkNumSetValues()
                        }
                    })
                }
            })
        })
    },
    addConstraints(label, renderer, widgetManager) {
        if (constraintsShown.value.length === 0) return
        renderer.getActors().forEach((actor) => {
            const ctfun = vtkColorTransferFunction.newInstance();
            ctfun.addRGBPoint(0, ...actor.getProperty().getColor()); // 0: default color has not been excluded
            ctfun.addRGBPoint(1, 0.2, 0.2, 0.2); // 1: gray has been excluded
            ctfun.setMappingRange(0, 1)
            ctfun.updateRange()

            const mapper = actor.getMapper()
            mapper.setLookupTable(ctfun)
            mapper.setColorByArrayName('color')

            const inputData = mapper.getInputData()
            const inputDataDomain = inputData.getFieldData().getArrayByName('domain').getData()[0]
            const bounds = inputData.getBounds()
            const allPoints = inputData.getPoints()
            const colorArray = vtkDataArray.newInstance({
                name: 'color',
                values: Array.from(
                    { length: allPoints.getNumberOfPoints() }, () => 0
                )
            })
            inputData.getPointData().addArray(colorArray)

            constraintInfo.value.forEach((cInfo) => {
                if (constraintsShown.value.includes(cInfo.id) && cInfo.domain === inputDataDomain) {
                    let cData = getConstraintLocation({ name: label }, cInfo)
                    const isCurrentPlacement = (
                        currentConstraintPlacement.value &&
                        currentConstraintPlacement.value.domain === cInfo.domain &&
                        currentConstraintPlacement.value.widgetID === cInfo.id
                    )

                    let widget;
                    let widgetState;
                    let widgetHandle;
                    if (cInfo.type === 'plane' && (cData || isCurrentPlacement)) {
                        // TODO: plane/shape overlap appears to change when rotating
                        // (but only in viewers without the mouse)
                        widget = vtkImplicitPlaneWidget.newInstance()
                        widget.placeWidget(bounds)
                        widget.setPlaceFactor(2)
                        widgetState = widget.getWidgetState()
                        widgetHandle = widgetManager.addWidget(widget)
                        // TODO: this doesn't disappear until after first interaction
                        widgetHandle.setOutlineVisible(false)
                        widgetHandle.getRepresentations()[0].setLabels({
                            'subject': label,
                            'domain': inputDataDomain
                        })
                        // TODO: can we increase the thickness of the normal line
                        // to make it easier to grab & manipulate?
                        widgetHandle.onEndInteractionEvent(() => {
                            setConstraintLocation({ name: label }, cInfo, {
                                type: 'plane',
                                data: {
                                    origin: widgetState.getOrigin(),
                                    normal: widgetState.getNormal(),
                                }
                            })
                            this.updateConstraintColors(label, inputData)
                        })

                        let origin = cData?.data?.origin
                        let normal = cData?.data?.normal
                        if (!origin) {
                            origin = [
                                (bounds[0] + bounds[1]) / 2,
                                (bounds[2] + bounds[3]) / 2,
                                (bounds[4] + bounds[5]) / 2,
                            ]
                        }
                        if (!normal) normal = [0, 0, 1]
                        if (isCurrentPlacement) {
                            // New placement started, initialize cData with defaults
                            setConstraintLocation({ name: label }, cInfo, {
                                type: 'plane',
                                data: { origin, normal }
                            })
                        }
                        widgetState.setOrigin(origin)
                        widgetState.setNormal(normal)
                    } else if (cInfo.type === 'paint' && isCurrentPlacement) {
                        // TODO: cannot rotate scene after a paint has started, even after releasing focus
                        const manipulator = vtkPickerManipulator.newInstance();
                        manipulator.getPicker().addPickList(actor);
                        widget = vtkPaintWidget.newInstance({ manipulator });
                        widgetHandle = widgetManager.addWidget(widget)
                        widgetManager.grabFocus(widget);
                        widget.getWidgetState().setActive(true)
                        widgetHandle.onEndInteractionEvent(() => {
                            widget.getWidgetState().getTrailList().forEach((state) => {
                                const currentPoint = state.getOrigin()
                                if (currentPoint) {
                                    if (!cData) {
                                        cData = {
                                            type: 'paint',
                                            data: { field: {} }
                                        }
                                    }
                                    cData.data.field.points = []
                                    cData.data.field.scalars = []
                                    const allPoints = inputData.getPoints()
                                    const colorArray = inputData.getPointData().getArrayByName('color')
                                    for (let i = 0; i < allPoints.getNumberOfPoints(); i++) {
                                        const p = allPoints.getPoint(i)
                                        cData.data.field.points.push(p)
                                        const distance = Math.hypot(
                                            p[0] - currentPoint[0],
                                            p[1] - currentPoint[1],
                                            p[2] - currentPoint[2]
                                        )
                                        const painted = colorArray.getValue(i) || distance < constraintPaintRadius.value
                                        cData.data.field.scalars.push(painted ? 0 : 1)
                                    }
                                    setConstraintLocation({ name: label }, cInfo, cData)
                                    this.updateConstraintColors(label, inputData)
                                }
                            })
                        })
                    }
                }
            })
            this.updateConstraintColors(label, inputData)
        })
    },
    updateConstraintColors(label, inputData) {
        if (constraintsShown.value.length === 0) return
        // TODO: reduce number of redundant calls
        // TODO: fix occurrences of TypeError: model._openGLRenderer is undefined
        const allPoints = inputData.getPoints()
        const allPointColors = inputData.getPointData().getArrayByName('color')
        const newColorArray = Array.from(
            { length: allPoints.getNumberOfPoints() }, () => 0
        )
        const inputDataDomain = inputData.getFieldData().getArrayByName('domain').getData()[0]
        if (allSetConstraints.value && allSetConstraints.value[label] && allSetConstraints.value[label][inputDataDomain]) {
            const currShapeConstraints = Object.values(allSetConstraints.value[label][inputDataDomain])
            currShapeConstraints.forEach((cData) => {
                if (constraintsShown.value.includes(cData.id)) {
                    if (cData?.type === 'plane') {
                        const { normal, origin } = cData.data
                        let dot = (a, b) => a.map((x, i) => a[i] * b[i]).reduce((m, n) => m + n);
                        for (let i = 0; i < allPoints.getNumberOfPoints(); i++) {
                            const point = allPoints.getPoint(i)
                            const pointColor = newColorArray[i]
                            if (!pointColor) {
                                const dotProduct = dot(normal, [
                                    origin[0] - point[0],
                                    origin[1] - point[1],
                                    origin[2] - point[2],
                                ])
                                if (dotProduct <= 0) {
                                    // negative dotProduct means point is below plane
                                    newColorArray[i] = 1
                                }
                            }
                        }
                    } else if (cData?.type === 'paint') {
                        // TODO: this takes too long with many actors
                        const { scalars, points } = cData.data.field
                        const scalarPoints = points.map((p, i) => ({ x: p[0], y: p[1], z: p[2], s: scalars[i] }))
                        const tree = new kdTree(scalarPoints, distance, ['x', 'y', 'z', 's']);
                        if (scalars.length === allPoints.getNumberOfPoints()) {
                            for (let i = 0; i < scalars.length; i++) {
                                const currentPoint = allPoints.getPoint(i)
                                const currentPointObj = {
                                    x: currentPoint[0],
                                    y: currentPoint[1],
                                    z: currentPoint[2],
                                }
                                const nearests = tree.nearest(currentPointObj, 1)
                                if (nearests.length) {
                                    const [nearest,] = nearests[0]
                                    // scalar assignment is swapped in stored constraint data
                                    if (nearest.s === 0) {
                                        newColorArray[i] = 1
                                    }
                                }
                            }
                        }
                    }
                }
            })
        }

        allPointColors.setData(newColorArray)
        inputData.modified()
    },
    addPoints(label, renderer, points, i) {
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

            if (data[i]) {
                const widgetManager = vtkWidgetManager.newInstance()
                widgetManager.setRenderer(renderer)
                let label = data[i][0]
                if (layersShown.value.includes('Landmarks')) {
                    this.addLandmarks(label, renderer, widgetManager)
                }
                if (layersShown.value.includes('Constraints')) {
                    this.addConstraints(label, renderer, widgetManager)
                }
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
