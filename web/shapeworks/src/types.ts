
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';


export interface ShapeData {
    points: vtkPolyData,
    shape: number,
}

export interface Dataset {
    id: number,
    file: string,
    created: string,
    modified: string,
    name: string,
    license: string,
    description: string,
    acknowledgement: string
}
