import vtkPLYReader from 'vtk.js/Sources/IO/Geometry/PLYReader';import readImageArrayBuffer from 'itk/readImageArrayBuffer';
import axios from 'axios';

// vtkITKImageReader.setReadImageArrayBufferFromITK(readImageArrayBuffer);


export default async function (url: string, filename='') {
    const arrayBuffer = (await axios.get(url, {
        responseType: 'arraybuffer'
    })).data;
    // if(filename.toLowerCase().endsWith('ply')){
    const reader = vtkPLYReader.newInstance();
    await reader.parseAsArrayBuffer(arrayBuffer)
    const data = reader.getOutputData();
    data.getPointData().setActiveScalars('does-not-exist');
    return data;
    // }
  }
