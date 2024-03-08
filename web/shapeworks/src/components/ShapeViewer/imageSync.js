import vtkImageMapper from 'vtk.js/Sources/Rendering/Core/ImageMapper';
import vtkImageSlice from 'vtk.js/Sources/Rendering/Core/ImageSlice';

import { ref, watch } from 'vue'
import {
    imageViewMode,
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
    addImage(imageData, renderer) {
        imageViewMode.value = true
        const sliceActor = vtkImageSlice.newInstance();
        const imageMapper = vtkImageMapper.newInstance();

        imageMapper.setInputData(imageData);
        sliceActor.setMapper(imageMapper);
        renderer.addActor(sliceActor);

        sliceActor.getProperty().setColorWindow(imageViewWindow.value)
        sliceActor.getProperty().setColorLevel(imageViewLevel.value)

        // Set default axis value to trigger other changes
        if (!imageViewAxis.value) {
            imageViewAxis.value = 'Z'
        }

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

        slices.value.push({
            sliceActor,
            imageMapper,
            renderer,
        })
    },
    imageViewModeUpdated() {
        // resize render window when visibility of image render options changes
        this.resize();
        this.render();
    },
    imageViewAxisUpdated() {
        slices.value.forEach(({ sliceActor, imageMapper, renderer }) => {
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
            renderer.resetCamera()
        })
        this.render()
    },
    imageViewSliceUpdated() {
        if (!imageViewAxis.value) {
            return undefined
        }
        slices.value.forEach(({ imageMapper }) => {
            if (['X', 'L'].includes(imageViewAxis.value)) {
                imageMapper.setISlice(imageViewSlices.value.x);
            } else if (['Y', 'P'].includes(imageViewAxis.value)) {
                imageMapper.setJSlice(imageViewSlices.value.y);
            } else if (['Z', 'S'].includes(imageViewAxis.value)) {
                imageMapper.setKSlice(imageViewSlices.value.z);
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
    watchImageStates() {
        watch(imageViewMode, this.imageViewModeUpdated)
        watch(imageViewAxis, this.imageViewAxisUpdated)
        watch(imageViewSlices, this.imageViewSliceUpdated, { deep: true })
        watch(imageViewWindow, this.imageViewWindowUpdated)
        watch(imageViewLevel, this.imageViewLevelUpdated)
    }
}
