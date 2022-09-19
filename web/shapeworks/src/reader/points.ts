import vtkPolyData from 'vtk.js/Sources/Common/DataModel/PolyData';

export default async function (url: string | undefined) {
  if(!url) return vtkPolyData.newInstance()
  const resp = await fetch(url);
  const data = await resp.text();
  const lines = data.trim().split('\n');
  const pointArray = lines.map((l) => l.trim().split(/\s+/).map((f) => parseFloat(f))).flat();
  const points = Float32Array.from(pointArray);

  const polyData = vtkPolyData.newInstance();
  polyData.getPoints().setData(points, 3);
  return polyData;
}
