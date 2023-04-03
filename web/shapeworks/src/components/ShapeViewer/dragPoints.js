import macro from 'vtk.js/Sources/macros';
import vtkPlaneManipulator from 'vtk.js/Sources/Widgets/Manipulators/PlaneManipulator';

function vtkMeshManipulator(publicAPI, model) {
    model.classHierarchy.push('vtkMeshManipulator');
    publicAPI.handleEvent = (callData, glRenderWindow) =>
        console.log(callData, glRenderWindow)
}

function extend(publicAPI, model, initialValues = {}) {
    vtkPlaneManipulator.extend(
        publicAPI, model, { ...initialValues },
    );
    vtkMeshManipulator(publicAPI, model);
}


export default class PointDrag {
    constructor() {
        this.manipulator = macro.newInstance(extend, 'vtkMeshManipulator')()
        console.log(this.manipulator)
    }

}
