import { ref } from '@vue/composition-api'
import {
    selectedProject,
    groomedShapesForOriginalDataObjects,
    reconstructionsForOriginalDataObjects,
    particlesForOriginalDataObjects
} from '.';

export const layers = ref<Record<string, any>[]>([
    {
        name: 'Original',
        color: 'white',
        rgb: [1, 1, 1],
        available: () => true,
    },
    {
        name: 'Groomed',
        color: 'green',
        rgb: [0, 1, 0],
        available: () => {
            return Object.values(groomedShapesForOriginalDataObjects.value)
            .map((obj) => Object.values(obj).flat()).flat().length > 0
        }
    },
    {
        name: 'Reconstructed',
        color: 'red',
        rgb: [1, 0, 0],
        available: () => {
            return reconstructionsForOriginalDataObjects.value?.length > 0
        },
    },
    {
        name: 'Particles',
        color: undefined,
        rgb: undefined,
        available: () => {
            return Object.values(particlesForOriginalDataObjects.value)
            .map((obj) => Object.values(obj).flat()).flat().length > 0
        }
    },
    {
        name: 'Landmarks',
        color: undefined,
        rgb: undefined,
        available: () => {
            return selectedProject.value?.landmarks && selectedProject.value.landmarks.length > 0
        }
    }
])



export const vtkShapesByType = ref<Record<string, any[]>>({
    "Original": [],
    "Groomed": [],
    "Reconstructed": [],
    "Particles": []
})
