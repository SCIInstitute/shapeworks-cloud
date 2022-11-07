
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';


export interface ShapeData {
    points: vtkPolyData,
    shape: vtkPolyData | vtkImageData,
}

export interface Project {
    id: number,
    file: string,
    created: string,
    modified: string,
    keywords: string,
    description: string,
    dataset: number,
    last_cached_analysis: Object | undefined,
}

export interface Dataset {
    id: number,
    file: string,
    created: string,
    modified: string,
    name: string,
    license: string,
    description: string,
    acknowledgement: string,
    projects: Project[],
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
    created: string,
    modified: string,
}

export interface Particles {
    id: number,
    groomed_mesh: GroomedShape,
    groomed_segmentation: GroomedShape,
    shape_model: number,
    local: string,
    transform: string,
    world: string,
    created: string,
    modified: string,
}

export interface GroomedShape {
    id: number,
    file: string,
    pre_alignment: string,
    pre_cropping: string,
    project: number,
    segmentation: number,
    mesh: number,
    created: string,
    modified: string,
}

export interface ReconstructedSample {
    id: number,
    file: string,
    project: number,
    particles: Particles,
}
