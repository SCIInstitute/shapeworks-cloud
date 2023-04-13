import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
// import vtkDataArray from 'vtk.js/Sources/Common/Core/DataArray';


export default function generateMapper(shape: vtkPolyData | vtkImageData) {
    const mapper = vtkMapper.newInstance();

    if (shape.getClassName() == 'vtkPolyData') {
        mapper.setInputData(shape as vtkPolyData);
    } else if (shape.getClassName() == 'vtkImageData') {
        console.error("Unexpected analysis mesh type");
    }

    return mapper;
}   