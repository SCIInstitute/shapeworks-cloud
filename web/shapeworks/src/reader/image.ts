import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkPLYReader from 'vtk.js/Sources/IO/Geometry/PLYReader';
import vtkPolyDataReader from 'vtk.js/Sources/IO/Legacy/PolyDataReader';
import readImageArrayBuffer from 'itk/readImageArrayBuffer';
import ITKHelper from 'vtk.js/Sources/Common/DataModel/ITKHelper';
import axios from 'axios';
import shapeReader from './shape'

const { convertItkToVtkImage } = ITKHelper;


export default async function (
    url: string | undefined, filename=''
): Promise<vtkImageData | vtkPolyData> {
    if(!url) return vtkPolyData.newInstance()

    const arrayBuffer = (await axios.get(url, {
        responseType: 'arraybuffer'
    })).data;

    if(
        filename.toLowerCase().endsWith('ply')){
        const reader = vtkPLYReader.newInstance();
        await reader.parseAsArrayBuffer(arrayBuffer)
        return reader.getOutputData();
    } else if (
        filename.toLowerCase().endsWith('nrrd') ||
        filename.toLowerCase().endsWith('nii') ||
        filename.toLowerCase().endsWith('nii.gz')
    ) {
        const { image } = await readImageArrayBuffer(null, arrayBuffer, filename)
        return convertItkToVtkImage(image)
    } else if (filename.toLowerCase().endsWith('vtp')) {
        return shapeReader(url)
    } else if (filename.toLowerCase().endsWith('vtk')) {
        const reader = vtkPolyDataReader.newInstance();
        await reader.setUrl(url)
        return reader.getOutputData();
    } else {
        console.log('Unknown file type for', filename)
        return vtkPolyData.newInstance()
    }
  }
