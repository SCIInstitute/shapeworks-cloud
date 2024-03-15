import vtkImageMapper from 'vtk.js/Sources/Rendering/Core/ImageMapper';
import vtkImageSlice from 'vtk.js/Sources/Rendering/Core/ImageSlice';
import vtkCutter from 'vtk.js/Sources/Filters/Core/Cutter';
import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
import vtkPlane from 'vtk.js/Sources/Common/DataModel/Plane';
import vtkActor from 'vtk.js/Sources/Rendering/Core/Actor';
import vtkProperty from 'vtk.js/Sources/Rendering/Core/Property';

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
        const plane = vtkPlane.newInstance();
        const cutter = vtkCutter.newInstance();
        const cutMapper = vtkMapper.newInstance();
        const cutActor = vtkActor.newInstance();

        sliceActor.setMapper(imageMapper);
        renderer.addActor(sliceActor);

        cutter.setCutFunction(plane);
        cutMapper.setInputConnection(cutter.getOutputPort());
        cutActor.setMapper(cutMapper);

        const cutProperty = cutActor.getProperty();
        cutProperty.setRepresentation(vtkProperty.Representation.WIREFRAME);
        cutProperty.setLighting(false);
        cutProperty.setColor(0, 1, 0);
        cutProperty.setLineWidth(5);
        cutActor.setVisibility(false);

        const slice = {
            renderer,
            sliceActor,
            imageMapper,
            plane,
            cutter,
            cutMapper,
            cutActor,
        }
        slices.value.push(slice)
        return slice
    },
    updateSlice(slice) {
        const { sliceActor, imageMapper, renderer, plane } = slice;

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
            this.updateCuttingPlane(imageMapper, plane)
        }
        renderer.resetCamera()
    },
    updateCuttingPlane(imageMapper, plane) {
        const sliceBounds = imageMapper.getBoundsForSlice()
        let origin = [sliceBounds[0], sliceBounds[2], sliceBounds[4]]
        let normal = [0, 0, 0]
        normal[imageMapper.getSlicingMode()] = 1
        plane.setOrigin(origin)
        plane.setNormal(normal)
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
        slices.value.forEach(({ imageMapper, plane }) => {
            if (['X', 'L'].includes(imageViewAxis.value)) {
                imageMapper.setISlice(imageViewSlices.value.x);
            } else if (['Y', 'P'].includes(imageViewAxis.value)) {
                imageMapper.setJSlice(imageViewSlices.value.y);
            } else if (['Z', 'S'].includes(imageViewAxis.value)) {
                imageMapper.setKSlice(imageViewSlices.value.z);
            }
            if (imageViewIntersectMode.value) {
                this.updateCuttingPlane(imageMapper, plane)
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
        slices.value.forEach(({ cutActor, cutter, renderer, imageMapper, plane }) => {
            const intersectionShape = renderer.getActors().find((actor) => actor.getClassName() != "vtkImageSlice")
            if (intersectionShape) {
                this.updateCuttingPlane(imageMapper, plane)
                cutActor.setVisibility(imageViewIntersectMode.value)
                intersectionShape.setVisibility(!imageViewIntersectMode.value)
                cutter.setInputData(intersectionShape.getMapper().getInputData())
                renderer.addActor(cutActor);
            }
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
        imageViewIntersectMode.value = false
    }
}
