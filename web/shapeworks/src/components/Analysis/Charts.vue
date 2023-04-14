<script lang="ts">
import { defineComponent } from '@vue/composition-api'
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

export default defineComponent({
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
});
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

</style>
  