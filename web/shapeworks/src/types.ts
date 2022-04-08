
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';


export interface ShapeData {
    points: vtkPolyData,
    shape: vtkPolyData | vtkImageData,
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

export interface Subject {
    id: number,
    name: string,
    dataset: number,
    created: string,
    modified: string,
}

export interface DataObject {
    type: string,
    id: number,
    subject: number,
    file: string,
    modality: string,
    anatomy_type: string,
}

export interface Particles {
    id: number,
    groomed_mesh: number,
    groomed_segmentation: number,
    shape_model: number,
    local: string,
    transform: string,
    world: string,
}

export interface GroomedShape {
    id: number,
    file: string,
    pre_alignment: string,
    pre_cropping: string,
    project: number,
    segmentation: number,
    mesh: number,
}
