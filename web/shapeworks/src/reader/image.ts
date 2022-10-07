import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkPLYReader from 'vtk.js/Sources/IO/Geometry/PLYReader';
import vtkPolyDataReader from 'vtk.js/Sources/IO/Legacy/PolyDataReader';
import vtkStringArray from 'vtk.js/Sources/Common/Core/StringArray'
import readImageArrayBuffer from 'itk/readImageArrayBuffer';
import ITKHelper from 'vtk.js/Sources/Common/DataModel/ITKHelper';
import axios from 'axios';
import shapeReader from './shape'

import { vtkShapesByType } from '@/store';

const { convertItkToVtkImage } = ITKHelper;


export default async function (
    url: string | undefined, filename='', type="Original",
): Promise<vtkImageData | vtkPolyData> {
    let shape: vtkImageData | vtkPolyData = vtkPolyData.newInstance()
    if(!url) return shape

    const arrayBuffer = (await axios.get(url, {
        responseType: 'arraybuffer'
    })).data;

    if(
        filename.toLowerCase().endsWith('ply')){
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
    } else {
        console.log('Unknown file type for', filename)
        shape = vtkPolyData.newInstance()
    }

    vtkShapesByType.value[type].push(shape)
    return shape
  }
