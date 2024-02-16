function crossProduct(v1, v2) {
    return [
        (v1[1] * v2[2] - v1[2] * v2[1]),
        (v1[2] * v2[0] - v1[0] * v2[2]),
        (v1[0] * v2[1] - v1[1] * v2[0]),
    ]
}

function addVectors(v1, v2) {
    return [
        v1[0] + v2[0],
        v1[1] + v2[1],
        v1[2] + v2[2],
    ]
}

function subtractVectors(v1, v2) {
    return [
        v1[0] - v2[0],
        v1[1] - v2[1],
        v1[2] - v2[2],
    ]
}

function normalizeVector(v) {
    const magnitude = Math.sqrt(
        Math.pow(v[0], 2) +
        Math.pow(v[1], 2) +
        Math.pow(v[2], 2)
    )
    return [
        v[0] / magnitude,
        v[1] / magnitude,
        v[2] / magnitude,
    ]
}

export default async function (url: string | undefined) {
    const constraintList: {type: string, data: any, name: string}[] = []
    if (url) {
        const resp = await fetch(url);
        const json = await resp.json()
        json.planes?.forEach(({points, name}) => {
            // must contain 3 points
            if (points && points.length === 3) {
                const [p1, p2, p3] = points
                const v1 = subtractVectors(p1, p3)
                const v2 = subtractVectors(p1, p2)
                // v1 and v2 are parallel to plane, normal is vector product of v1 and v2
                const normal = normalizeVector(crossProduct(v1, v2))
                const origin = p1
                constraintList.push({
                    type: 'plane',
                    data : { origin, normal },
                    name
                })
            }
        })
        if (json.free_form_constraints) {
            constraintList.push({
                type: 'paint',
                data: json.free_form_constraints,
                name: json.free_form_constraints.name,
            })
        }
    }
    return constraintList
}



export function convertConstraintDataForDB(shapeLocations, shapeInfos) {
    const constraintJSON: Record<string, any> = {}
    shapeInfos.forEach((cInfo) => {
        const indexForShape = shapeInfos
            .filter((info) => info.type === cInfo.type && info.domain === cInfo.domain)
            .findIndex((info) => info.id === cInfo.id)
        const locations = shapeLocations.filter((cData) => cData.type === cInfo.type)

        // location not set, skip this iteration
        if (locations.length <= indexForShape) return
        const cData = locations[indexForShape]
        if (cInfo.type === 'plane') {
            if (!constraintJSON.planes) constraintJSON.planes = []
            const { origin, normal } = cData.data

            const v1 = crossProduct(normal, [1, 0, 0])
            const v2 = crossProduct(normal, [0, 1, 0])

            const p1 = origin;
            const p2 = addVectors(origin, normal[2] > 0 ? v2 : v1)
            const p3 = addVectors(origin, normal[2] > 0 ? v1 : v2)

            const planeData: Record<string, any> = {points: [p1, p2, p3]}
            if (cInfo.name) {
                planeData.name = cInfo.name
            }
            constraintJSON.planes.push(planeData)
        } else if (cInfo.type === 'paint') {
            const paintData: Record<string, any> = cData.data
            if (cInfo.name) {
                paintData.name = cInfo.name
            }
            constraintJSON.free_form_constraints = paintData
        }
    })

    return constraintJSON
}
