import { DataObject, Dataset, Subject } from '@/types'
import { ref } from '@vue/composition-api'

export const loadingState = ref<boolean>(false)

export const allDatasets = ref<Dataset[]>([])

export const selectedDataset = ref<Dataset>()

export const allSubjectsForDataset = ref<Subject[]>([])

export const selectedSubject = ref<Subject>()

export const allDataObjectsForSubject = ref<DataObject[]>([])
