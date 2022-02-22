import { Dataset } from '@/types'
import { ref } from '@vue/composition-api'

export const allDatasets = ref<Dataset[]>([])

export const selectedDataset = ref<Dataset>()
