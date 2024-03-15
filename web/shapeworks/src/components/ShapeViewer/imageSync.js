import vtkImageMapper from 'vtk.js/Sources/Rendering/Core/ImageMapper';
import vtkImageSlice from 'vtk.js/Sources/Rendering/Core/ImageSlice';
import vtkCutter from 'vtk.js/Sources/Filters/Core/Cutter';
import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
import vtkPlane from 'vtk.js/Sources/Common/DataModel/Plane';
import vtkActor from 'vtk.js/Sources/Rendering/Core/Actor';
import vtkProperty from 'vtk.js/Sources/Rendering/Core/Property';
import vtkCalculator from 'vtk.js/Sources/Filters/General/Calculator';
import vtkGlyph3DMapper from 'vtk.js/Sources/Rendering/Core/Glyph3DMapper';
import vtkSphereSource from 'vtk.js/Sources/Filters/Sources/SphereSource';
import { FieldDataTypes } from 'vtk.js/Sources/Common/DataModel/DataSet/Constants';
import { AttributeTypes } from 'vtk.js/Sources/Common/DataModel/DataSetAttributes/Constants';


import { ref, watch } from 'vue'
import {
    imageViewMode,
    imageViewIntersectMode,
    imageViewAxis,
    imageViewSlices,
    imageViewSliceRanges,
    imageViewWindow,
    imageViewWindowRange,
    imageViewLevel,
    imageViewLevelRange,
} from '@/store'

const slices = ref([])

export default {
    createSlice(renderer) {
        const sliceActor = vtkImageSlice.newInstance();
        const imageMapper = vtkImageMapper.newInstance();
        const cutPlane = vtkPlane.newInstance();
        const cutter = vtkCutter.newInstance();
        const cutMapper = vtkMapper.newInstance();
        const cutActor = vtkActor.newInstance();
        const particleFilter = vtkCalculator.newInstance();
        const filteredParticleSphere = vtkSphereSource.newInstance();
        const filteredParticleActor = vtkActor.newInstance();
        const filteredParticleMapper = vtkGlyph3DMapper.newInstance();

        sliceActor.setMapper(imageMapper);
        renderer.addActor(sliceActor);

        cutter.setCutFunction(cutPlane);
        cutMapper.setInputConnection(cutter.getOutputPort());
        cutActor.setMapper(cutMapper);

        const cutProperty = cutActor.getProperty();
        cutProperty.setRepresentation(vtkProperty.Representation.WIREFRAME);
        cutProperty.setLighting(false);
        cutProperty.setColor(0, 1, 0);
        cutProperty.setLineWidth(5);
        cutActor.setVisibility(false);


        particleFilter.setFormula({
            getArrays: () => ({
                input: [{
                    location: FieldDataTypes.COORDINATE,
                }],
                output: [{
                    location: FieldDataTypes.POINT,
                    name: 'visible',
                    dataType: Float32Array,
                    attribute: AttributeTypes.SCALARS,
                    numberOfComponents: 1,
                }]
            }),
            evaluate: (arraysIn, arraysOut) => {
                const [coords] = arraysIn.map((d) => d.getData());
                const [visible] = arraysOut.map((d) => d.getData());

                const imageBounds = imageMapper.getBounds()
                const sliceBounds = imageMapper.getBoundsForSlice()
                let currentAxis;
                let axisBounds;
                let axisSliceBounds;
                switch (imageMapper.getSlicingMode) {
                    case 0:
                        currentAxis = 'x';
                        axisBounds = imageBounds.slice(0, 2);
                        axisSliceBounds = sliceBounds.slice(0, 2);
                        break;
                    case 1:
                        currentAxis = 'y'
                        axisBounds = imageBounds.slice(2, 4)
                        axisSliceBounds = sliceBounds.slice(2, 4)
                        break;
                    default:
                        currentAxis = 'z'
                        axisBounds = imageBounds.slice(4, 6)
                        axisSliceBounds = sliceBounds.slice(4, 6)
                        break;
                }
                const sliceRange = imageViewSliceRanges.value[currentAxis]
                const numSlices = sliceRange[1] - sliceRange[0]
                const sliceThickness = (axisBounds[1] - axisBounds[0]) / numSlices

                axisSliceBounds[1] += sliceThickness
                for (var i = 0; i < visible.length; i++) {
                    const location = coords.slice(i * 3, i * 3 + 3)
                    const axisCoord = location[imageMapper.getSlicingMode()]
                    if (
                        axisCoord >= axisSliceBounds[0] &&
                        axisCoord < axisSliceBounds[1]
                    ) {
                        visible[i] = 1
                    }
                }

                arraysOut.forEach(x => x.modified())
            }
        })
        filteredParticleMapper.setScaleModeToScaleByMagnitude();
        filteredParticleMapper.setScaleFactor(this.glyphSize);
        filteredParticleMapper.setScaleArray('visible')
        filteredParticleMapper.setInputConnection(particleFilter.getOutputPort(), 0)
        filteredParticleMapper.setInputConnection(filteredParticleSphere.getOutputPort(), 1)
        filteredParticleActor.setMapper(filteredParticleMapper);

        const slice = {
            renderer,
            sliceActor,
            imageMapper,
            cutPlane,
            cutter,
            cutMapper,
            cutActor,
            particleFilter,
            filteredParticleMapper,
            filteredParticleActor,
        }
        slices.value.push(slice)
        return slice
    },
    updateSlice(slice) {
        const { sliceActor, imageMapper, renderer } = slice;

        let cameraPosition, cameraDirection, cameraViewUp;
        const camera = renderer.getActiveCamera();
        const center = sliceActor.getCenter();
        const distance = camera.getDistance();

        if (['X', 'L'].includes(imageViewAxis.value)) {
            imageMapper.setSlicingMode('I');
            imageMapper.setISlice(imageViewSlices.value.x);
            cameraPosition = [
                center[0] + distance,
                center[1],
                center[2],
            ]
            cameraDirection = [-1, 0, 0]
            cameraViewUp = [0, 1, 0]
        } else if (['Y', 'P'].includes(imageViewAxis.value)) {
            imageMapper.setSlicingMode('J');
            imageMapper.setJSlice(imageViewSlices.value.y);
            cameraPosition = [
                center[0],
                center[1] + distance,
                center[2],
            ]
            cameraDirection = [0, -1, 0]
            cameraViewUp = [0, 0, -1]
        } else if (['Z', 'S'].includes(imageViewAxis.value)) {
            imageMapper.setSlicingMode('K');
            imageMapper.setKSlice(imageViewSlices.value.z);
            cameraPosition = [
                center[0],
                center[1],
                center[2] + distance,
            ]
            cameraDirection = [0, 0, -1]
            cameraViewUp = [0, 1, 0]
        }

        if (cameraPosition && cameraDirection && cameraViewUp) {
            camera.setPosition(...cameraPosition)
            camera.setDirectionOfProjection(...cameraDirection)
            camera.setViewUp(...cameraViewUp)
        }

        if (imageViewIntersectMode.value) {
            this.updateCuttingPlane(slice)
        }
        renderer.resetCamera()
    },
    updateIntersection(slice) {
        // TODO: account for multidomain cases
        const { renderer, cutter, cutActor, filteredParticleActor, particleFilter } = slice

        const intersectionShape = renderer.getActors().find((actor) => actor.getClassName() != "vtkImageSlice")
        if (intersectionShape) {
            cutter.setInputData(intersectionShape.getMapper().getInputData())
            cutActor.setVisibility(imageViewIntersectMode.value)
            intersectionShape.setVisibility(!imageViewIntersectMode.value)
            renderer.addActor(cutActor);
        }


        // If particles shown, filter by slice bounds
        const particles = renderer.getActors().map(
            (a) => ({
                mapper: a.getMapper(),
                actor: a
            })
        ).find(
            ({ mapper }) => mapper.getClassName() === 'vtkGlyph3DMapper'
        )
        if (particles) {
            particles.actor.setVisibility(false);
            particleFilter.setInputData(particles.mapper.getInputData())
            filteredParticleActor.setVisibility(true)
            renderer.addActor(filteredParticleActor)
        } else {
            filteredParticleActor.setVisibility(false)
        }
        this.render()
    },
    updateCuttingPlane(slice) {
        const { imageMapper, cutPlane, particleFilter } = slice;

        const sliceBounds = imageMapper.getBoundsForSlice()
        let origin = [sliceBounds[0], sliceBounds[2], sliceBounds[4]]
        let normal = [0, 0, 0]
        normal[imageMapper.getSlicingMode()] = 1
        cutPlane.setOrigin(origin)
        cutPlane.setNormal(normal)

        // If filtering particles, call modified to trigger filter evaluation
        particleFilter.getInputData()?.modified()
    },
    updateGlyphSize(glyphSize) {
        slices.value.forEach(({ filteredParticleMapper }) => {
            filteredParticleMapper.setScaleFactor(glyphSize)
        })
        this.render()
    },
    addImage(imageData, renderer) {
        let slice = slices.value.find((s) => s.renderer == renderer)
        if (!slice) slice = this.createSlice(renderer)
        this.updateSlice(slice)

        imageViewMode.value = true
        slice.imageMapper.setInputData(imageData);
        slice.sliceActor.getProperty().setColorWindow(imageViewWindow.value)
        slice.sliceActor.getProperty().setColorLevel(imageViewLevel.value)

        const dataRange = imageData.getPointData().getScalars().getRange();
        imageViewLevelRange.value = dataRange
        imageViewLevel.value = (dataRange[1] - dataRange[0]) / 3 + dataRange[0]
        imageViewWindowRange.value = dataRange
        imageViewWindow.value = (dataRange[1] - dataRange[0]) / 2 + dataRange[0]

        const extent = imageData.getExtent();
        imageViewSliceRanges.value = {
            x: [extent[0], extent[1]],
            y: [extent[2], extent[3]],
            z: [extent[4], extent[5]],
        }

        if (imageViewIntersectMode.value) this.imageViewIntersectModeUpdated()
    },
    imageViewModeUpdated() {
        // resize render window when visibility of image render options changes
        this.resize();
        this.render();
    },
    imageViewAxisUpdated() {
        slices.value.forEach((slice) => {
            this.updateSlice(slice)
        })
        this.render()
    },
    imageViewSliceUpdated() {
        if (!imageViewAxis.value) {
            return undefined
        }
        slices.value.forEach((slice) => {
            const { imageMapper } = slice;

            if (['X', 'L'].includes(imageViewAxis.value)) {
                imageMapper.setISlice(imageViewSlices.value.x);
            } else if (['Y', 'P'].includes(imageViewAxis.value)) {
                imageMapper.setJSlice(imageViewSlices.value.y);
            } else if (['Z', 'S'].includes(imageViewAxis.value)) {
                imageMapper.setKSlice(imageViewSlices.value.z);
            }
            if (imageViewIntersectMode.value) {
                this.updateCuttingPlane(slice)
            }
        })
        this.render()
    },
    imageViewWindowUpdated() {
        slices.value.forEach(({ sliceActor }) => {
            sliceActor.getProperty().setColorWindow(imageViewWindow.value)
        })
        this.render()
    },
    imageViewLevelUpdated() {
        slices.value.forEach(({ sliceActor }) => {
            sliceActor.getProperty().setColorLevel(imageViewLevel.value)
        })
        this.render()
    },
    imageViewIntersectModeUpdated() {
        slices.value.forEach((slice) => {
            this.updateIntersection(slice);
            this.updateCuttingPlane(slice);
        })
        this.render()
    },
    watchImageStates() {
        watch(imageViewMode, this.imageViewModeUpdated)
        watch(imageViewAxis, this.imageViewAxisUpdated)
        watch(imageViewSlices, this.imageViewSliceUpdated, { deep: true })
        watch(imageViewWindow, this.imageViewWindowUpdated)
        watch(imageViewLevel, this.imageViewLevelUpdated)
        watch(imageViewIntersectMode, this.imageViewIntersectModeUpdated)
    },
    resetImageSlices() {
        slices.value = []
    },
    resetIntersections() {
        slices.value.forEach(this.updateIntersection)
    }
}
