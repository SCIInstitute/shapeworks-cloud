// functions for generating analysis charts

export type lineChartProps = { 
    title: string, 
    x_label: string, 
    y_label: string, 
    x: Array<number>, 
    y: Array<number> 
}


/* 
* TODO: Add automatic resizing/css styling for chart class
* TODO: download data as CSV?
* TODO: copy data to clipboard
*/
export function lineChartOptions (data: lineChartProps) {
    return ({
        title: {
            text: data.title,
            textStyle: {
                color: "#ffffff"
            }
        },
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
    navigator.clipboard.writeText(text).then(function() {
        console.log('Async: Copying to clipboard was successful!');
    }, function(err) {
    console.error('Async: Could not copy text: ', err);
    });
}

function showData(data: lineChartProps) {
    let text = `# Modes:\t${data.y_label}\n`
        // TODO: better styling needed
    for (let i = 0; i < data.x.length; i++) {
        text += `${data.x[i]}\t\t\t${data.y[i]}\n`
    }
    
    const div = document.createElement('div');
    div.className = "dataview";

    const btn = document.createElement('button');
    btn.className = 'copy-button';
    btn.innerHTML = 'Copy';
    btn.onclick = () => copyData(text);

    const textarea = document.createElement('textarea');
    textarea.className = 'dataview-text';
    textarea.innerHTML = text;

    div.appendChild(textarea);
    div.appendChild(btn);

    // TODO: find alternative to textarea
    return (
        div
    );
}

