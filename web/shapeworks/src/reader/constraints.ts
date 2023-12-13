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
    const constraintList: {type: string, data: any}[] = []
    if (url) {
        const resp = await fetch(url);
        const json = await resp.json()
        json.planes?.forEach(({points}) => {
            // must contain 3 points
            if (points.length === 3) {
                const [p1, p2, p3] = points
                const v1 = subtractVectors(p1, p3)
                const v2 = subtractVectors(p1, p2)
                // v1 and v2 are parallel to plane, normal is vector product of v1 and v2
                const normal = normalizeVector(crossProduct(v1, v2))
                const origin = p1
                constraintList.push({
                    type: 'plane',
                    data : { origin, normal }
                })
            }
        })
        if (json.free_form_constraints) {
            constraintList.push({
                type: 'paint',
                data: json.free_form_constraints
            })
        }
    }
    return constraintList
}



export function convertConstraintDataForDB(constraintData) {
    const constraintJSON: Record<string, any> = {}
    constraintData.forEach((cData) => {
        if (cData.type === 'plane') {
            if (!constraintJSON.planes) constraintJSON.planes = []
            const { origin, normal } = cData.data

            const v1 = crossProduct(normal, [1, 0, 0])
            const v2 = crossProduct(normal, [0, 1, 0])

            const p1 = origin;
            const p2 = addVectors(origin, v2)
            const p3 = addVectors(origin, v1)

            constraintJSON.planes.push({points: [p1, p2, p3]})
        } else if (cData.type === 'paint') {
            constraintJSON.free_form_constraints = cData.data
        }
    })
    return constraintJSON
}
