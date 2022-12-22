// functions for generating analysis charts

/* TODO
* Add automatic resizing/css styling for chart class
*/
export function chartOptions (data: { title: string; x_label: string; x: Array<number>; y_label: string; y: Array<number> }) {
    return ({
        title: {
            text: data.title,
            textStyle: {
                color: "#ffffff"
            }
        },
        tooltip: {
            trigger: 'axis',
            formatter: 'Mode {b}<br />Value: {c}'
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


function showData(data: { title: string; x_label: string; x: Array<number>; y_label: string; y: Array<number> }) {
    let text = `# Modes:\t${data.y_label}\n`
        // TODO: better styling needed
        for (let i = 0; i < data.x.length; i++) {
            text += `${data.x[i]}\t\t\t${data.y[i]}\n`
        }

        return ('<textarea style="display: block; width: 100%; height: 100%; font-family: monospace; font-size: 14px; line-height: 1.6rem; resize: none; box-sizing: border-box; outline: none; color: rgb(0, 0, 0); border-color: rgb(51, 51, 51); background-color: rgb(255, 255, 255);">' +
                text +
                '</textarea>');
}