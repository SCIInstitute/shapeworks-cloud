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

// from https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
export function hexToRgb(hex: string) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16)
     ] : [0, 0, 0];
  }

export function distance(a, b){
    return Math.pow(a.x - b.x, 2) +  Math.pow(a.y - b.y, 2) +  Math.pow(a.z - b.z, 2);
}
