
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

export interface AnalysisParams {
    range: number,
    steps: number,
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

export interface AnalysisMeanShape {
    file: string,
    particles: string,
}

export interface Analysis {
    id: number,
    created: string,
    modified: string,
    charts: AnalysisChart[],
    good_bad_angles: number[][],
    groups: AnalysisGroup[],
    mean_shapes: AnalysisMeanShape[],
    modes: AnalysisMode[],
}

export interface Project {
    id: number,
    creator: number,
    name: string,
    file: string,
    file_contents: Object | undefined,
    private: boolean,
    readonly: boolean,
    thumbnail: string,
    created: string,
    modified: string,
    keywords: string,
    description: string,
    dataset: number,
    landmarks: Landmarks[],
    landmarks_info: any,
    constraints: Constraints[],
    last_cached_analysis: Analysis | undefined,
}

export interface Dataset {
    id: number,
    creator: number,
    name: string,
    file: string,
    private: boolean,
    thumbnail: string,
    created: string,
    modified: string,
    keywords: string,
    license: string,
    description: string,
    acknowledgement: string,
    projects: Project[],
    summary?: string,
}

export interface Subject {
    id: number,
    name: string,
    dataset: number,
    created: string,
    modified: string,
    groups: string[],
    showDetails: boolean,
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
    anatomy_type: string,
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
    anatomy_type: string
}

export interface Task {
    id: number | undefined,
    name: string,
    abort: boolean,
    percent_complete: number,
    error: string,
    message: string,
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
    anatomy_type: string,
}

export interface LandmarkInfo {
    id: number,
    name: string,
    color: number[],
    comment: string,
    domain: string,
    num_set: number,
    visible: "true" | "false",
}

export interface Constraints {
    id?: number,
    file?: string,
    type: string,
    project?: number,
    subject?: number,
    created?: string,
    modified?: string,
    anatomy_type?: string,
    domain?: string,
    num_set?: number,
}

export interface CacheComparison {
    file: string,
    particles: string
}

export interface AugmentationPair {
    sample_num: number,
    project: number,
    mesh: string,
    image: string,
    particles: string,
}

export interface TrainingPair {
    project: number,
    particles: string,
    scalar: string,
    mesh: string,
    index: string,
    example_type: string,
    validation: boolean,
}

export interface TestingData {
    project: number,
    particles: string,
    mesh: string,
    image_type: string,
    image_id: string,
}

export interface DeepSSMImage {
    project: number,
    index: string,
    image: string,
    validation: boolean,
}

export interface Filters {
    private: boolean,
    readonly: boolean,
}
