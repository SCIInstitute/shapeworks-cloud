// functions for generating analysis charts

export type lineChartProps = { 
    title: string, 
    x_label: string, 
    y_label: string, 
    x: Array<number>, 
    y: Array<number> 
}

export function lineChartOptions (data: lineChartProps) {
    return ({
        title: {
            text: data.title,
            textStyle: {
                color: "#ffffff"
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
            formatter: '# Modes {b}<br />Value: {c}' // b is x value, c is y value
        },
        toolbox: {
            show: true,
            orient: 'horizontal',
            showTitle: true,
            feature: {
                saveAsImage: {
                    type: 'svg',
                    name: data.title.toLowerCase() + "_chart",
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
                color: "#c3c3c3"
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
                color: "#c3c3c3"
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
    const csvarray = csvstring.split(/(?<=\n)/gi); // uses positive look-behind to keep \n intact after split

    const blob = new Blob(csvarray);

    return URL.createObjectURL(blob);
}

function getTextAsCSV(text: string) {
    // replace 1 or more consecutive tabs with a comma
    const csvstring = text.replaceAll(/\t+/ig, ",");

    const splitstring = csvstring.split('\n');

    splitstring.forEach((row, rowindex) => {
        if (row.search(/\s/ig) >= 0) { // if the current rwo contains any spaces or non-whitespace special char (\n\r\t\f)
            const h = row.split(',');
            h.forEach((value, i) => {
                h[i] = '"' + value + '"';
            });
            splitstring[rowindex] = h.join(',');
        }
    })
    
    return splitstring.join('\n');
}

function showData(data: lineChartProps) {
    let text = `# Modes:\t${data.y_label}\n`
    // TODO: better format needed. Maybe HTML table?
    for (let i = 0; i < data.x.length; i++) {
        text += `${data.x[i]}\t\t\t${data.y[i]}\n`
    }
    
    const div = document.createElement('div');
    div.className = "dataview";

    const copybtn = document.createElement('button');
    copybtn.className = 'dataview-button copy-button';
    copybtn.innerHTML = 'Copy to Clipboard';
    copybtn.onclick = () => copyData(text);

    const downloadbtn = document.createElement('button');
    downloadbtn.className = 'dataview-button download-button';
    downloadbtn.innerHTML = 'Download';

    const downloadlink = document.createElement('a');
    downloadlink.href = getDownloadURL(text);
    downloadlink.download = data.y_label.toLowerCase().replaceAll(" ", "_") + '.csv';

    downloadbtn.appendChild(downloadlink);
    downloadbtn.onclick = () => downloadlink.click();

    const textarea = document.createElement('textarea');
    textarea.className = 'dataview-text';
    textarea.innerHTML = text;

    div.appendChild(textarea);
    div.appendChild(copybtn);
    div.appendChild(downloadbtn);

    return (
        div
    );
}

