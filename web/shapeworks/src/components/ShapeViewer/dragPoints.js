import { throttle } from 'vtk.js/Sources/macros';
import vtkCubeSource from 'vtk.js/Sources/Filters/Sources/CubeSource';
import vtkActor from 'vtk.js/Sources/Rendering/Core/Actor';
import vtkCalculator from 'vtk.js/Sources/Filters/General/Calculator';
import { FieldDataTypes } from 'vtk.js/Sources/Common/DataModel/DataSet/Constants';
import { AttributeTypes } from 'vtk.js/Sources/Common/DataModel/DataSetAttributes/Constants';
import vtkGlyph3DMapper from 'vtk.js/Sources/Rendering/Core/Glyph3DMapper'
import { landmarkColorList } from '@/store'


// Inspired by https://kitware.github.io/vtk-js/examples/HardwareSelector.html
export default class PointDrag {
    constructor(renderer, renderWindow, renderArea, pointSet) {
        this.renderer = renderer
        this.renderWindow = renderWindow
        this.renderArea = renderArea

        // Create vis pipeline objects
        this.pointMapper = vtkGlyph3DMapper.newInstance({
            scaleMode: vtkGlyph3DMapper.SCALE_BY_CONSTANT,
            scaleFactor: 3
        });
        this.pointSource = vtkCubeSource.newInstance()
        this.colorFilter = this.colorPoints()
        this.colorFilter.setInputData(pointSet, 0);
        this.pointActor = vtkActor.newInstance();

        // Connect vis pipeline objects
        this.pointActor.setMapper(this.pointMapper);
        this.pointMapper.setInputData(pointSet, 0)
        this.pointMapper.setInputData(this.pointSource.getOutputData(), 1);
        this.pointMapper.setInputConnection(this.colorFilter.getOutputPort(), 0);
        this.renderer.addActor(this.pointActor)

        // Set up hardware selector
        this.interactor = this.renderWindow.getInteractor()
        this.interactorView = this.interactor.getView()
        this.hardwareSelector = this.interactorView.getSelector()
        this.hardwareSelector.setCaptureZValues(true);

        // Mouse listeners
        this.renderArea.addEventListener('mousedown', this.handleMouseDown.bind(this));
        // this.throttleMouseHandler = throttle(this.pickOnMouseEvent.bind(this), 20);
        // this.renderArea.addEventListener('mousemove', this.throttleMouseHandler);
    }

    colorPoints() {
        const filter = vtkCalculator.newInstance()
        filter.setFormula({
            getArrays() {
                return {
                    input: [{ location: FieldDataTypes.COORDINATE }],
                    output: [{
                        location: FieldDataTypes.POINT,
                        name: 'color',
                        dataType: 'Uint8Array',
                        attribute: AttributeTypes.SCALARS,
                        numberOfComponents: 3,
                    }],
                };
            },
            evaluate(input, output) {
                const [coords] = input.map((d) => d.getData());
                const [color] = output.map((d) => d.getData());
                const n = coords.length / 3;
                for (let i = 0; i < n; i += 1) {
                    let c = [0, 0, 0]
                    if (landmarkColorList.value[i]) {
                        c = landmarkColorList.value[i]
                    }
                    color[3 * i] = c[0];
                    color[3 * i + 1] = c[1];
                    color[3 * i + 2] = c[2];
                }
                input.forEach((x) => x.modified());
            },
        });
        return filter
    }

    handleMouseDown(event) {
        if (this.renderArea.contains(event.target)) {
            const [x, y] = this.eventToWindowXY(event);
            if (x && y) {
                this.hardwareSelector.getSourceDataAsync(
                    this.renderer, x, y, x, y
                ).then((result) => {
                    if (result) {
                        this.processSelections(result.generateSelection(x, y, x, y));
                    }
                });
            }
        }
    }

    processSelections(selections) {
        console.log('process selections', selections)
        if (!selections || selections.length === 0) {
            return;
        }
        const {
            worldPosition,
            prop,
        } = selections[0].getProperties();
        console.log('picked!!', worldPosition, prop)
        this.renderWindow.render()
    }

    eventToWindowXY(event) {
        const boundingRect = event.target.getBoundingClientRect()
        const clickLocation = {
            x: event.clientX - boundingRect.x,
            y: event.clientY - boundingRect.y
        }
        const currRendererProportion = this.renderer.getViewport()
        const currClickProportion = [
            clickLocation.x / boundingRect.width,
            clickLocation.y / boundingRect.height
        ]
        const clickedInCurrentRenderer = (
            currClickProportion[0] > currRendererProportion[0]
            && currClickProportion[0] < currRendererProportion[2]
            && currClickProportion[1] > currRendererProportion[1]
            && currClickProportion[1] < currRendererProportion[3]
        )
        if (clickedInCurrentRenderer) {
            const x = clickLocation.x
            const y = clickLocation.y // Need to flip Y
            console.log(x, y)
            return [x, y];
        }
        return [undefined, undefined]
    }
}
