<script lang="ts">
  import { analysis, analysisFileShown, cacheAllComparisons, currentAnalysisFileParticles, meanAnalysisFileParticles } from '@/store';
  import { computed, defineComponent, ref, Ref, watch, inject } from '@vue/composition-api';
  import { AnalysisTabs } from './util';
  
  export default defineComponent({
    props: {
      currentTab: String,
      openTab: Number
    },
    setup(props) {
      const mode = ref(1);
      const stdDev = ref(0);

      const menu = ref();
      const params = ref({
        stdDevRange: {
          min: 0,
          max: 0,
          step: 0,
          numSteps: 0
        }
      });

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
        if (!analysis.value || !currMode.value) return {min: 0, max: 0, step: 0, numSteps: 0}
        const pcaValues = currMode.value.pca_values.map(p => p.pca_value)
        const min =  Math.min(...pcaValues);
        const max =  Math.max(...pcaValues);
        const step = (max - min) / pcaValues.length;
        const numSteps = Math.round((max - min) / step);
        params.value.stdDevRange = {min, max, step, numSteps}
        return {
            min, max, step, numSteps
        }
      })

      const pcaInfo = computed(() => {
        return {
            headers: [
                {text: 'key', value: 'key'},
                {text: 'value', value: 'value', align: 'end'}
            ],
            items: [
                {key: 'Lambda', value:currPCA.value ? Math.round(currPCA.value.lambda_value * 100) / 100 : 0},
                {key: 'Eigenvalue', value: currMode.value ? Math.round(currMode.value.eigen_value * 100) / 100 : 0},
                {key: 'Explained Variance', value: currMode.value ? Math.round(currMode.value.explained_variance * 100) / 100 : 0, class: 'percentage'},
                {key: 'Cumulative Explained Variance', value: currMode.value ? Math.round(currMode.value.cumulative_explained_variance * 100) / 100 : 0, class:'percentage'},
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
                const { min, max } = stdDevRange.value;

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
        submitParams() {
          const { min, max, step, numSteps } = params.value.stdDevRange;
          
          // if the new params are within the currently loaded range in analysis
          stdDevRange.value.min = min;
          stdDevRange.value.max = max;
          stdDevRange.value.step = step;
          stdDevRange.value.numSteps = numSteps;

          // otherwise, spawn a new analysis job with the provided parameters as options
          // DEPENDS: shapeworks offline analysis command update
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
        params,
        pcaInfo,
        animate,
        menu,
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
      <v-row justify="space-between">
        <v-slider
          v-model="stdDev"
          :min="stdDevRange.min"
          :max="stdDevRange.max"
          :step="stdDevRange.step"
          ticks="always"
          tick-size="4"
          thumb-label
          track-color="#aaa"
          track-fill-color="#aaa"
          label="Std. Devs. from Mean"
        />
        <v-menu
          v-model="menu"
          :close-on-content-click="false"
          bottom
          right
        >
          <template v-slot:activator="{ on, attrs }">
            <v-btn
              dark
              icon
              v-bind="attrs"
              v-on="on"
            >
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </template>
          <v-list style="margin: auto">
            <v-list-item>
              <v-list-item-content>
                  <v-text-field
                    v-model="params.stdDevRange.min"
                    type="number"
                    step="1.0"
                    min="-10.0"
                    max="9.0"
                    label="Std. Dev. Min"
                    hide-details
                  />
              </v-list-item-content>
            </v-list-item>
            <v-list-item>
              <v-list-item-content>
                  <v-text-field
                    v-model="params.stdDevRange.max"
                    type="number"
                    step="1.0"
                    max="10.0"
                    min="-9.0"
                    label="Std. Dev. Max"
                    hide-details
                  />
              </v-list-item-content>
            </v-list-item>
            <v-list-item>
              <v-list-item-content>
                  <v-text-field
                    v-model="params.stdDevRange.numSteps"
                    type="number"
                    step="1.0"
                    min="1.0"
                    max="100.0"
                    label="Number of steps"
                    hide-details
                    @change="params.stdDevRange.step = (params.stdDevRange.max - params.stdDevRange.min) / params.stdDevRange.numSteps"
                  />
              </v-list-item-content>
            </v-list-item>
          </v-list>
          <div class="justifyAround" style="margin: auto">
            <v-btn small color="secondary" @click="menu = false">Cancel</v-btn>
            <v-btn small color="primary" @click="methods.submitParams(); menu = false;">{{(true) ? "Submit" : "Re-compute"}}</v-btn>
          </div>
        </v-menu>
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
  