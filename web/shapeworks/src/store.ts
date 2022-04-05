import { DataObject, Dataset, Subject, Particles } from '@/types'
import { getDataset } from '@/api/rest';
import { ref } from '@vue/composition-api'

export const loadingState = ref<boolean>(false)

export const allDatasets = ref<Dataset[]>([])

export const selectedDataset = ref<Dataset>()

export const allSubjectsForDataset = ref<Subject[]>([])

export const allDataObjectsInDataset = ref<DataObject[]>([])

export const selectedDataObjects = ref<DataObject[]>([])

export const showParticles = ref<boolean>(true)

export const particleSize = ref<number>(2)

export const particlesForOriginalDataObjects = ref<Record<string, Record<number, Particles>>>({})

export const geometryShown = ref<string>("Original")

export const loadDataset = async (datasetId: number) => {
    // Only reload if something has changed
    if (selectedDataset.value?.id != datasetId) {
        loadingState.value = true;
        selectedDataset.value = await getDataset(datasetId);
        loadingState.value = false;
    }
}
