// Helper functions that may come in handy in component or view files

export function groupBy(xs: any[], key: string) {
    return xs.reduce(function(rv, x) {
        (rv[x[key]] = rv[x[key]] || []).push(x);
        return rv;
    }, {});
}

export function shortDateString(date: string) {
    return date.split('T')[0]
}

export function shortFileName(file: string) {
    const split = file.split('?')[0].split('/')
    return split[split.length-1]
}

export function getDistance(
    one: number[], two: number[], signed=false
){
    let dimSum = 0
    let squaredDimSum = 0
    for (let i = 0; i< one.length; i++){
        const d = two[i] - one[i]
        dimSum += d
        squaredDimSum += d * d
    }
    if (signed && dimSum < 0) {
        return -Math.sqrt(squaredDimSum);
    }
    return Math.sqrt(squaredDimSum);
}
