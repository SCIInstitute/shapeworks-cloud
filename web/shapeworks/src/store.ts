import { DataObject, Dataset, Subject } from '@/types'
import { getDataset, getSubject } from '@/api/rest';
import { ref } from '@vue/composition-api'

export const loadingState = ref<boolean>(false)

export const allDatasets = ref<Dataset[]>([])

export const selectedDataset = ref<Dataset>()

export const allSubjectsForDataset = ref<Subject[]>([])

export const selectedSubject = ref<Subject>()

export const allDataObjectsForSubject = ref<DataObject[]>([])

export const selectedDataObjects = ref<DataObject[]>([])

export const loadDatasetAndSubject = async (datasetId: number, subjectId: number) => {
    // Only reload if something has changed
    if (selectedDataset.value?.id != datasetId || selectedSubject.value?.id != subjectId) { 
        loadingState.value = true;
        selectedDataset.value = await getDataset(datasetId);
        selectedSubject.value = await getSubject(subjectId);
        loadingState.value = false;
    }
}