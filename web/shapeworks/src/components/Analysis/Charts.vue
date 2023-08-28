<script lang="ts">
import { use } from 'echarts/core';
import { SVGRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  ToolboxComponent,
  DataZoomComponent
} from 'echarts/components';
import VChart from 'vue-echarts';
import { lineChartOptions } from './charts'
import { AnalysisChart } from '@/types';

// registers required echarts components
use([SVGRenderer,LineChart,TitleComponent,TooltipComponent,GridComponent,ToolboxComponent,DataZoomComponent]);

export default {
    name: "Charts",
    props: {
      charts: {
        type: Array,
        default: () => [],
        validator: (value: any) => {
          // Check that every item in the array is a valid AnalysisChart object
          return value.every((chart: any) => {
            return (
              typeof chart === 'object' &&
              chart !== null &&
              typeof chart.title === 'string' &&
              typeof chart.type === 'string' &&
              typeof chart.x_label === 'string' &&
              typeof chart.y_label === 'string' &&
              chart.x.every((val: any) => typeof val === 'number') &&
              chart.y.every((val: any) => typeof val === 'number')
            );
          });
        },
        required: true
      }
    },
    components: {
      VChart
    },
    setup(props) {
      const data = {};

      const methods = {
        generateChart: (index: number) => {
            return lineChartOptions(props.charts[index] as AnalysisChart);
        }
      };

      const computed = {};

      const init = () => {};

      init();

      return {
        data,
        methods,
        computed,
      };
    },
};
</script>

<template>
    <div v-if="charts.length > 0">
      <v-chart class="chart" v-for="chart, index in charts" :key="chart.title" :option="methods.generateChart(index)" />
    </div>
    <div v-else>
      No charts generated...
    </div>
</template>

<style>
  .chart {
      height: 400px;
      width: 400px;
  }

  .dataview {
      height: 100%;
      width: 100%;
  }

  .datatable {
      color: #000000;
      width: 100%;
  }

  .datatable tbody tr:nth-child(even) {
      background-color: #e5e4e2;
  }

  .datatable-row td {
      padding-right: 30px;
  }

  .dataview-button {
      background: #2196f3;
      border-radius: 3px;
      cursor: pointer;
      padding: 2px 5px;
      font-size: 12px;
      z-index: 1;
  }

  .dataview-button:hover {
      background: #318dd8;
  }

  .copy-button {
      position: absolute;
      bottom: 5px;
      right: 70px;
  }

  .download-button {
      position: absolute;
      bottom: 5px;
      right: 185px;
  }

  .dataview-text {
      display: block;
      height: 100%;
      width: 100%;
      font-family: monospace;
      font-size: 14px;
      line-height: 1.6rem;
      resize: none;
      border: 1px solid #333333;
  }
</style>
