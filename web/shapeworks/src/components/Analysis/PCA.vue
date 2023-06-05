<script lang="ts">
  import { analysis, analysisFileShown, cacheAllComparisons, currentAnalysisFileParticles, meanAnalysisFileParticles } from '@/store';
  import { computed, defineComponent, ref, Ref, watch, inject } from 'vue';
  import { AnalysisTabs } from './util';

  export default defineComponent({
    props: {
      currentTab: String,
      openTab: Number
    },
    setup(props) {
      const mode = ref(1);
      const stdDev = ref(0);

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

      const currPCA = computed(() => {
          return currMode.value?.pca_values.find(
              p => p.pca_value.toPrecision(2) === stdDev.value.toPrecision(2)
          )
      })

      const stdDevRange = computed(() => {
          if (!analysis.value || !currMode.value) return [0, 0, 0]
          const pcaValues = currMode.value.pca_values.map(p => p.pca_value)
          const min =  Math.min(...pcaValues);
          const max =  Math.max(...pcaValues)
          const step = (max - min) / pcaValues.length
          return [
              min, max, step
          ]
      })

      const pcaInfo = computed(() => {
          return {
              headers: [
                  {text: 'key', value: 'key'},
                  {text: 'value', value: 'value', align: 'end'}
              ],
              items: [
                  {key: 'Lambda', value: currPCA.value?.lambda_value || 0},
                  {key: 'Eigenvalue', value: currMode.value?.eigen_value},
                  {key: 'Explained Variance', value: currMode.value?.explained_variance, class: 'percentage'},
                  {key: 'Cumulative Explained Variance', value: currMode.value?.cumulative_explained_variance, class:'percentage'},
              ],
          }
      })

      const methods = {
        updateFileShown() {
            let fileShown = undefined
            let particles = undefined
            if (props.currentTab === 'analyze' && analysis.value){
                if (stdDev.value === 0) {
                    fileShown = analysis.value.mean_shape
                    particles = analysis.value.mean_particles;
                } else {
                    fileShown = currPCA.value?.file
                    particles = currPCA.value?.particles
                }
            }
            currentAnalysisFileParticles.value = particles;
            meanAnalysisFileParticles.value =  analysis.value?.mean_particles;
            analysisFileShown.value = fileShown;
        },
        async cacheAllPCAComparisons() {
          if (currMode.value !== undefined) {
            const allInMode = currMode.value.pca_values;

            await cacheAllComparisons(allInMode);
          }
        },
        animateSlider() {
            if (props.openTab === AnalysisTabs.PCA) { // PCA tab animate
                const [ min, max ] = stdDevRange.value;

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
              step = stdDevRange.value[2];
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
        }
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
      };
    },
  });
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
      <v-slider
        v-model="stdDev"
        :min="stdDevRange[0]"
        :max="stdDevRange[1]"
        :step="stdDevRange[2]"
        ticks="always"
        tick-size="4"
        thumb-label
        track-color="#aaa"
        track-fill-color="#aaa"
        label="Std. Devs. from Mean"
      />
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

</style>
