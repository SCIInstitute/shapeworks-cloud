import vtkPLYReader from 'vtk.js/Sources/IO/Geometry/PLYReader';

export default async function (url) {
    const reader = vtkPLYReader.newInstance();
    await reader.setUrl(url, { binary: true });
    return reader.getOutputData();
}
