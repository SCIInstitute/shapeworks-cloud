import vtkXMLPolyDataReader from 'vtk.js/Sources/IO/XML/XMLPolyDataReader';

export default async function (url) {
    const reader = vtkXMLPolyDataReader.newInstance();
    await reader.setUrl(url, { binary: true });
    const data = reader.getOutputData();
    data.getPointData().setActiveScalars('does-not-exist');
    return data;
}
