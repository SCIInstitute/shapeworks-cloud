import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkPLYReader from 'vtk.js/Sources/IO/Geometry/PLYReader';
import vtkSTLReader from 'vtk.js/Sources/IO/Geometry/STLReader';
import vtkPolyDataReader from 'vtk.js/Sources/IO/Legacy/PolyDataReader';
import vtkStringArray from 'vtk.js/Sources/Common/Core/StringArray'
import vtkDataArray from 'vtk.js/Sources/Common/Core/DataArray';
import readImageArrayBuffer from 'itk/readImageArrayBuffer';
import ITKHelper from 'vtk.js/Sources/Common/DataModel/ITKHelper';
import axios from 'axios';
import shapeReader from './shape'


import { vtkShapesByType, deepSSMErrorGlobalRange } from '@/store';

const { convertItkToVtkImage } = ITKHelper;


async function readDeepSSMScalars(url: string | undefined) {
    if(!url) return vtkDataArray.newInstance({
        name: 'deepssm_error'
    })

    const reader = vtkPolyDataReader.newInstance();
    await reader.setUrl(url);
    const data = reader.getOutputData();

    const content = (await axios.get(url)).data;
    const values: number[] = []
    content.split('\r\n\r').forEach((section) => {
        if (section.includes('deepssm_error')) {
            const [header, data] = section.split('deepssm_error')
            const line_values = data.slice(1).split('\r\n').map((line) => {
                return line.split(' ').map((v) => parseFloat(v)).filter((v) => v)
            }).pop()
            if (line_values) {
                values.push(...line_values)
            }
        }
    })
    const dataRange = [
        Math.min(...values),
        Math.max(...values),
    ]
    deepSSMErrorGlobalRange.value = [
        Math.min(deepSSMErrorGlobalRange.value[0], dataRange[0]),
        Math.max(deepSSMErrorGlobalRange.value[1], dataRange[1]),
    ]

    const arr = vtkDataArray.newInstance({
        name: 'deepssm_error',
        values
    })
    return arr 
}


export default async function (
    url: string | undefined, filename='', type="Original", metadata={},
): Promise<vtkImageData | vtkPolyData> {
    let shape: vtkImageData | vtkPolyData = vtkPolyData.newInstance()
    if(!url) return shape

    const arrayBuffer = (await axios.get(url, {
        responseType: 'arraybuffer'
    })).data;

    if(filename.toLowerCase().endsWith('ply')){
        const reader = vtkPLYReader.newInstance();
        await reader.parseAsArrayBuffer(arrayBuffer)
        shape =  reader.getOutputData();
    } else if (
        filename.toLowerCase().endsWith('nrrd') ||
        filename.toLowerCase().endsWith('nii') ||
        filename.toLowerCase().endsWith('nii.gz')
    ) {
        const { image } = await readImageArrayBuffer(null, arrayBuffer, filename)
        shape = convertItkToVtkImage(image)
    } else if (filename.toLowerCase().endsWith('vtp')) {
        shape = await shapeReader(url)
    } else if (filename.toLowerCase().endsWith('vtk')) {
        const reader = vtkPolyDataReader.newInstance();
        await reader.setUrl(url)
        shape = reader.getOutputData();
    } else if (filename.toLowerCase().endsWith('stl')) {
        const reader = vtkSTLReader.newInstance();
        await reader.parseAsArrayBuffer(arrayBuffer)
        shape =  reader.getOutputData();
    } else {
        console.log('Unknown file type for', filename)
        shape = vtkPolyData.newInstance()
    }

    // Add metadata to field data
    const fieldData = shape.getFieldData()
    Object.entries(metadata).forEach(([key, value]) => {
        // @ts-ignore
        const str: string = value.toString()
        const arr = vtkStringArray.newInstance({
            name: key,
            size: 1,
        })
        arr.setData([str], 1)
        // @ts-ignore
        fieldData.addArray(arr)
    })
    if (type === 'DeepSSM') {
        const arr = await readDeepSSMScalars(url)
        shape.getPointData().addArray(arr)
    }

    vtkShapesByType.value[type].push(shape)
    return shape
  }
