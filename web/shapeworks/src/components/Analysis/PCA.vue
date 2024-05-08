<script lang="ts">
  import { computed, ref, Ref, watch, inject } from 'vue';
  import { AnalysisTabs } from './util';
  import { CacheComparison } from '@/types';
import { groupBy } from '../../helper';
  import {
    analysis,
    analysisFilesShown,
    cacheAllComparisons,
    currentAnalysisParticlesFiles,
    meanAnalysisParticlesFiles,
    selectedProject,
  } from '@/store';

  export default {
    props: {
      currentTab: String,
      openTab: Number
    },
    setup(props) {
      const mode = ref(1);
      const stdDev = ref(0);

      const menu = ref();

      const showConfirmation = ref(false);

      let step = 0;
      let intervalId: number;

      const currentlyCaching: Ref | undefined = inject('currentlyCaching');
      const animate = ref<boolean>(false);

      const modeOptions = computed(() => {
        return analysis.value?.modes.sort((a, b) => a.mode - b.mode)
      })

      const currMode = computed(() => {
        return analysis.value?.modes.find((m) => m.mode == mode.value)
      })

      const currPCAs = computed(() => {
        return currMode.value?.pca_values.filter(
            p => p.pca_value.toPrecision(2) === stdDev.value.toPrecision(2)
        )
      })

      const stdDevRange = computed(() => {
        if (!analysis.value || !currMode.value) return {range: 0.0, step: 0.0, numSteps: 0}
        const pcaValues = currMode.value.pca_values.map(p => Math.round(p.pca_value * 100) / 100)
        const numDomains = analysis.value.mean_shapes.length || 1
        const min =  Math.min(...pcaValues);
        const max =  Math.max(...pcaValues);
        const range = max;
        const step = (max - min) / (pcaValues.length / numDomains);
        const numSteps = Math.round((max - min) / step) + 1;

        return {
            range, step, numSteps
        }
      })

      const pcaInfo = computed(() => {
        return {
            headers: [
                {text: 'key', value: 'key'},
                {text: 'value', value: 'value', align: 'end'}
            ],
            items: [
                {key: 'Lambda', value: currPCAs.value?.length ? Math.round(currPCAs.value[0].lambda_value * 100) / 100 : 0},
                {key: 'Eigenvalue', value: currMode.value ? Math.round(currMode.value.eigen_value * 100) / 100 : 0},
                {key: 'Explained Variance', value: currMode.value ? Math.round(currMode.value.explained_variance * 100) / 100 : 0, class: 'percentage'},
                {key: 'Cumulative Explained Variance', value: currMode.value ? Math.round(currMode.value.cumulative_explained_variance * 100) / 100 : 0, class:'percentage'},
            ],
        }
      })

      const methods = {
        updateFileShown() {
            let filesShown: string[] = []
            let particles: string[] = []
            if (props.currentTab === 'analyze' && analysis.value){
              if (stdDev.value === 0) {
                filesShown = analysis.value.mean_shapes.map((m) => m.file)
                particles = analysis.value.mean_shapes.map((m) => m.particles);
              } else if (currPCAs.value) {
                filesShown = currPCAs.value.map(p => p.file)
                particles = currPCAs.value.map(p => p.particles)
              }
            }
            currentAnalysisParticlesFiles.value = particles;
            meanAnalysisParticlesFiles.value =  analysis.value?.mean_shapes.map((m) => m.particles);
            analysisFilesShown.value = filesShown;
        },
        async cacheAllPCAComparisons() {
          if (currMode.value !== undefined) {
            const allInMode: CacheComparison[][] = Object.values(groupBy(currMode.value.pca_values, 'pca_value'));
            await cacheAllComparisons(allInMode);
          }
        },
        animateSlider() {
            if (props.openTab === AnalysisTabs.PCA) { // PCA tab animate
                const { range } = stdDevRange.value;
                const min = range * -1;
                const max = range;

                if (stdDev.value <= min) {
                  stdDev.value = min;
                  step *= -1;
                } else if (stdDev.value >= max) {
                  stdDev.value = max;
                  step *= -1;
                }

                stdDev.value = parseFloat((stdDev.value + step).toFixed(1));

            }
        },
        async triggerAnimate() {
            if (currMode.value === undefined || animate === undefined) return;

            if (animate.value && currentlyCaching) {
              step = stdDevRange.value.step;
              currentlyCaching.value = true;
              await methods.cacheAllPCAComparisons();
              currentlyCaching.value = false;
              intervalId = setInterval(methods.animateSlider, 500);
            }
            if (animate.value === false && intervalId) {
              clearInterval(intervalId);
            }
        },
        stopAnimating() {
          animate.value = false;
        },
      }

      const init = () => {
        methods.updateFileShown();
      }

      init();

      watch(props, methods.updateFileShown)
      watch(analysis, methods.updateFileShown)

      watch(mode, () => {
        methods.updateFileShown();
        animate.value = false;
      })

      watch(stdDev, methods.updateFileShown)
      if (animate) {
        watch(animate, methods.triggerAnimate)
      }

      return {
        methods,
        modeOptions,
        mode,
        stdDev,
        stdDevRange,
        pcaInfo,
        animate,
        menu,
        showConfirmation,
        selectedProject,
      };
    },
  };
</script>

<template>
    <div>
      <v-select
        label="Select mode"
        v-model="mode"
        :items="modeOptions"
        item-text="mode"
        item-value="mode"
      />
      <v-row justify="space-between">
        <v-slider
          v-model="stdDev"
          :min="stdDevRange.range * -1"
          :max="stdDevRange.range"
          :step="stdDevRange.step"
          ticks="always"
          tick-size="4"
          thumb-label
          track-color="#aaa"
          track-fill-color="#aaa"
          label="Std. Devs. from Mean"
        >
          <template v-slot:thumb-label>
            {{ Math.round(stdDev * 100) / 100 }}
          </template>
        </v-slider>
      </v-row>
      <v-row justify="center">
          <v-checkbox
              class="mt-0 mb-8 pt-0"
              v-model="animate"
              label="Animate"
              hide-details
          ></v-checkbox>
      </v-row>
      <br/>
      <v-data-table
        :headers="pcaInfo.headers"
        :items="pcaInfo.items"
        item-class="class"
        hide-default-header
        hide-default-footer
      />
    </div>
</template>

<style>
  .justifyAround {
    display: flex;
    justify-content: space-around;
  }
</style>
