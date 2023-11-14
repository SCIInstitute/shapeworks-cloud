

export default async function (url: string | undefined) {
    const constraintList: {type: string, data: any}[] = []
    if (url) {
        const resp = await fetch(url);
        const json = await resp.json()
        json.planes?.forEach(({points}) => {
            // must contain 3 points
            if (points.length === 3) {
                const [p1, p2, p3] = points
                const v1 = [
                    p2[0] - p3[0],
                    p2[1] - p3[1],
                    p2[2] - p3[2],
                ]
                const v2 = [
                    p1[0] - p2[0],
                    p1[1] - p2[1],
                    p1[2] - p2[2],
                ]
                // v1 and v2 are parallel to plane, normal is vector product of v1 and v2
                const normal = [
                    (v1[1] * v2[2] - v1[2] * v2[1]),
                    (v1[2] * v2[0] - v1[0] * v2[2]),
                    (v1[0] * v2[1] - v1[1] * v2[0]),
                ]
                // TODO: determine better origin
                const origin = p1
                constraintList.push({
                    type: 'plane',
                    data : { origin, normal }
                })
            }
        })
    }
    return constraintList
}
