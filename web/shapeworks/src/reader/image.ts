import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkPLYReader from 'vtk.js/Sources/IO/Geometry/PLYReader';
import readImageArrayBuffer from 'itk/readImageArrayBuffer';
import ITKHelper from 'vtk.js/Sources/Common/DataModel/ITKHelper';
import axios from 'axios';
import shapeReader from './shape'

const { convertItkToVtkImage } = ITKHelper;


export default async function (
    url: string, filename=''
): Promise<vtkImageData | vtkPolyData> {
    const arrayBuffer = (await axios.get(url, {
        responseType: 'arraybuffer'
    })).data;
    if(filename.toLowerCase().endsWith('ply')){
        const reader = vtkPLYReader.newInstance();
        await reader.parseAsArrayBuffer(arrayBuffer)
        return reader.getOutputData();
    } else if (filename.toLowerCase().endsWith('nrrd')) {
        const { image } = await readImageArrayBuffer(null, arrayBuffer, filename)
        return convertItkToVtkImage(image)
    } else if (filename.toLowerCase().endsWith('vtp')) {
        return shapeReader(url)
    }
    return vtkImageData.newInstance()
  }
