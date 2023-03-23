
import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';
import vtkImageData from 'vtk.js/Sources/Common/DataModel/ImageData';
import vtkOpenGLRenderWindow from 'vtk.js/Sources/Rendering/OpenGL/RenderWindow';
import vtkRenderWindow from 'vtk.js/Sources/Rendering/Core/RenderWindow';
import vtkRenderWindowInteractor from 'vtk.js/Sources/Rendering/Core/RenderWindowInteractor';
import vtkRenderer from 'vtk.js/Sources/Rendering/Core/Renderer';
import vtkMapper from 'vtk.js/Sources/Rendering/Core/Mapper';
import vtkOrientationMarkerWidget from 'vtk.js/Sources/Interaction/Widgets/OrientationMarkerWidget';


export interface VTKInstance {
    renderWindow: vtkRenderWindow,
    openglRenderWindow: vtkOpenGLRenderWindow,
    interactor: vtkRenderWindowInteractor,
    orientationCube: vtkOrientationMarkerWidget,
    renderers: vtkRenderer[],
    pointMappers: vtkMapper[],
}

export interface ShapeData {
    points: vtkPolyData,
    shape: vtkPolyData | vtkImageData,
}

export interface AnalysisPCA {
    id: number,
    pca_value: number,
    file: string,
    particles: string,
    lambda_value: number,
}

export interface AnalysisMode {
    id: number,
    mode: number,
    eigen_value: number,
    explained_variance: number,
    cumulative_explained_variance: number,
    pca_values: AnalysisPCA[],
}

export interface AnalysisChart {
    title: string, 
    x_label: string, 
    y_label: string, 
    x: Array<number>, 
    y: Array<number>,
}

export interface AnalysisGroup {
    id: number,
    name: string,
    group1: string,
    group2: string,
    file: string,
    particles: string,
    ratio: number,
}

export interface Analysis {
    id: number,
    created: string,
    modified: string,
    charts: AnalysisChart[],
    groups: AnalysisGroup[],
    mean_shape: string,
    mean_particles: string;
    modes: AnalysisMode[],
}

export interface Project {
    id: number,
    file: string,
    created: string,
    modified: string,
    keywords: string,
    description: string,
    dataset: number,
    landmarks: Landmarks[],
    landmarks_info: any,
    last_cached_analysis: Analysis | undefined,
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

export interface Task {
    id: number | undefined,
    name: string,
    percent_complete: number,
    error: string,
    created: string,
    modified: string,
}

export interface Landmarks {
    id: number,
    file: string,
    project: number,
    subject: number,
    created: string,
    modified: string,
}
