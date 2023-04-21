import { AnalysisChart } from "./types";

// functions for generating analysis charts
export function lineChartOptions (data: AnalysisChart) {
    // decimal place rounding could be specified for each chart
    const decimalPlaces = 3;

    // rounds each y value to specified decimal place
    // x will always be integer
    data.y.forEach((n, i) => {
        data.y[i] = roundTo(n, decimalPlaces);
    });

    return ({
        title: {
            text: data.title,
            textStyle: {
                color: "#999999"
            }
        },
        dataZoom: [
            {
                id: 'xAxisZoom',
                type: 'inside',
                xAxisIndex: [0]
            },
        ],
        tooltip: {
            trigger: 'axis',
            formatter: '# Modes: {b}<br />Value: {c}' // b is x value, c is y value
        },
        toolbox: {
            show: true,
            orient: 'horizontal',
            showTitle: true,
            feature: {
                saveAsImage: {
                    type: 'svg',
                    name: data.title.toLowerCase() + "_chart",
                    excludedComponents: ['toolbox', 'title'],
                },
                dataView: {
                    show: true,
                    title: "View Data",
                    readOnly: true,
                    optionToContent: () => showData(data)
                },
                dataZoom: {
                    show: true,
                },
                restore: {
                    show: true
                },
            }
        },
        xAxis: {
            type: 'category',
            name: data.x_label,
            nameLocation: 'center',
            nameTextStyle: {
                padding: [5,0,0,0],
                color: "#bbbbbb"
            },
            axisLabel: {
                align: 'center',
                color: "#a3a3a3"
            },
            boundaryGap: false,
            splitLine: {
                show: true,
                lineStyle: {
                    type: "dashed",
                    opacity: 0.5,
                }
            },
            data: data.x
        },
        yAxis: {
            name: data.y_label,
            nameTextStyle: {
                align: 'left',
                color: "#bbbbbb"
            },
            axisLine: {
                show: true
            },
            axisLabel: {
                align: 'right',
                color: "#a3a3a3"
            },
            axisTick: {
                lineStyle: {
                    color: "#a3a3a3"
                }
            },
            scale: true,
            splitLine: {
                show: true,
                lineStyle: {
                    type: "dashed",
                    opacity: 0.5,
                }
            },
        },
        series: {
            type:'line',
            data: data.y
        }
    })
}

function copyData(text: string) {
    const CSVText = getTextAsCSV(text);
    navigator.clipboard.writeText(CSVText).then(function() {
        console.log('Copying to clipboard was successful!');
    }, function(err) {
    console.error('Could not copy data: ', err);
    });
}

function getDownloadURL(text: string) {
    const csvstring = getTextAsCSV(text);
    // const csvarray = csvstring.split(/(?<=\n)/gi); // uses positive look-behind to keep \n intact after split
    // this should do the same thing without the look-behind
    const csvarray = csvstring.split(/\n/g).map((v, idx) => idx ? v + '\n' : v);

    const blob = new Blob(csvarray);

    return URL.createObjectURL(blob);
}

function getTextAsCSV(text: string) {
    const splitstring = text.split('\n');

    splitstring.forEach((row, rowindex) => {
        if (row.search(/\s/ig) >= 0) { // if the current row contains any spaces or non-whitespace special char (\n\r\t\f)
            const h = row.split(',');
            h.forEach((value, i) => {
                h[i] = '"' + value + '"';
            });
            splitstring[rowindex] = h.join(',');
        }
    })

    return splitstring.join('\n');
}

function showData(data: AnalysisChart) {
    const dataTable = document.createElement('TABLE');
    dataTable.className = 'datatable'
    const thead = document.createElement('thead');
    dataTable.appendChild(thead);
    const theadRow = thead.insertRow(0);
    theadRow.className = 'datatable-row';
    const theadOne = theadRow.insertCell(0);
    theadOne.innerHTML = '<b># Modes</b>';
    const theadTwo = theadRow.insertCell(1);
    theadTwo.innerHTML = `<b>${data.y_label}</b>`;
    const tbody = document.createElement('tbody');
    dataTable.appendChild(tbody);

    let csvtext = `# Modes:,${data.y_label}\n`

    for (let i = 0; i < data.x.length; i++) {
        const row = tbody.insertRow(-1); // -1 index == last position
        row.className = 'datatable-row';
        const cellOne = row.insertCell(0);
        cellOne.innerHTML = `${data.x[i]}`;
        const cellTwo = row.insertCell(1);
        cellTwo.innerHTML = `${data.y[i]}`;

        csvtext += `${data.x[i]},${data.y[i]}\n`
    }

    const div = document.createElement('div');
    div.className = "dataview";

    const copybtn = document.createElement('button');
    copybtn.className = 'dataview-button copy-button';
    copybtn.innerHTML = 'Copy to Clipboard';
    copybtn.onclick = () => copyData(csvtext);

    const downloadbtn = document.createElement('button');
    downloadbtn.className = 'dataview-button download-button';
    downloadbtn.innerHTML = 'Download';

    const downloadlink = document.createElement('a');
    downloadlink.href = getDownloadURL(csvtext);
    downloadlink.download = data.y_label.toLowerCase().replaceAll(" ", "_") + '.csv';

    downloadbtn.appendChild(downloadlink);
    downloadbtn.onclick = () => downloadlink.click();

    div.appendChild(dataTable);
    div.appendChild(copybtn);
    div.appendChild(downloadbtn);

    return (
        div
    );
}

function roundTo(num: number, place: number) {
    const factor = 10 ** place;
    return Math.round(num * factor) / factor;
}
