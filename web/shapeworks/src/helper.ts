// Helper functions that may come in handy in component or view files

/**
 * Groups an array of objects by a specified key.
 * @param xs The array of objects to be grouped.
 * @param key The key to group the objects by.
 * @returns An object where the keys are unique values of the specified key, and the values are arrays of objects with that key value.
 */
export function groupBy(xs: any[], key: string) {
    return xs.reduce(function(rv, x) {
        (rv[x[key]] = rv[x[key]] || []).push(x);
        return rv;
    }, {});
}

/**
 * Returns the short date string from a given date string.
 * @param date The date string.
 * @returns The short date string.
 */
export function shortDateString(date: string) {
    return date.split('T')[0]
}

/**
 * Returns the short file name from a given file path.
 * @param file The file path.
 * @returns The short file name.
 */
export function shortFileName(file: string) {
    const split = file.split('?')[0].split('/')
    return split[split.length-1]
}

/**
 * Calculates the Euclidean distance between two points in n-dimensional space.
 * @param one The coordinates of the first point.
 * @param two The coordinates of the second point.
 * @param signed (Optional) Whether to return a signed distance. Defaults to false.
 * @returns The Euclidean distance between the two points.
 */
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

/**
 * Converts a hexadecimal color code to an RGB array.
 * @param hex The hexadecimal color code.
 * @returns The RGB array representation of the color.
 */
export function hexToRgb(hex: string) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16)
    ] : [0, 0, 0];
}

export function rgbToHex(rgb) {
    const components = rgb.map((c) => {
        const hex = c.toString(16);
        return hex.length == 1 ? "0" + hex : hex;
    })
    return "#" + components.join("");
  }

export function distance(a, b){
    return Math.pow(a.x - b.x, 2) +  Math.pow(a.y - b.y, 2) +  Math.pow(a.z - b.z, 2);
}

/**
 * Parses a CSV file from the specified URL and returns the data as an array of objects.
 * @param url - The URL of the CSV file to parse.
 * @returns A promise that resolves to an array of objects representing the CSV data.
 */
export async function parseCSVFromURL(url: string) {
    return fetch(url)
    .then(response => response.text())
    .then(text => {
        // last value of the substring is blank, so we remove it
        const splitstring = text.split('\n').slice(0, -1);

        const data: {[x: string]: any} = [];
        for (let i = 1; i < splitstring.length; i++) {
            const d = {};
            const row = splitstring[i].split(',');
            for (let j = 0; j < row.length; j++) {
                // parseFloat if row[j] is a number, otherwise keep it as a string
                d[j] = isNaN(parseFloat(row[j])) ? row[j] : parseFloat(row[j]);
            }
            data.push(d);
        }
        return data;
    })
}
