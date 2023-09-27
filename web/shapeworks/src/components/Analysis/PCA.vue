<script lang="ts">
  import { computed, ref, Ref, watch, inject } from 'vue';
  import { AnalysisTabs } from './util';
  import { AnalysisParams, CacheComparison } from '@/types';
import { groupBy } from '../../helper';
  import {
    analysis,
    analysisFilesShown,
    cacheAllComparisons,
    currentAnalysisParticlesFiles,
    currentTasks,
    meanAnalysisParticlesFiles,
    selectedProject,
    spawnJob,
    spawnJobProgressPoll
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

      const message: Ref = inject('message') || ref('');
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

      const params = ref<AnalysisParams>(stdDevRange.value)

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
        // spawn an analysis job when params are changed
        async submitParams() {
          const { range, numSteps } = params.value;

          if (!selectedProject.value) return;

          if (!currentTasks.value[selectedProject.value.id]) {
              currentTasks.value[selectedProject.value.id] = {}
          }

          const taskIds = await spawnJob("analyze", {"analysis": {range, steps: numSteps}}); // Record<string, any>

          if(!taskIds || taskIds.length === 0) {
              message.value = `Failed to submit analysis job.`
              setTimeout(() => message.value = '', 10000)
          } else {
              message.value = `Successfully submitted analysis job. Awaiting results...`
              currentTasks.value[selectedProject.value.id] = taskIds

              spawnJobProgressPoll()
          }
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
        showConfirmation
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
                    v-model="params.range"
                    type="number"
                    step="1.0"
                    max="10.0"
                    min="1.0"
                    label="Std. Dev. Range"
                    hide-details
                  />
              </v-list-item-content>
            </v-list-item>
            <v-list-item>
              <v-list-item-content>
                  <v-text-field
                    v-model="params.numSteps"
                    type="number"
                    step="1.0"
                    min="1.0"
                    max="100.0"
                    label="Number of steps"
                    hide-details
                    @change="params.step = (params.range) / params.numSteps"
                  />
              </v-list-item-content>
            </v-list-item>
          </v-list>
          <div class="justifyAround" style="margin: auto">
            <v-btn small color="secondary" @click="menu = false">Cancel</v-btn>
            <v-btn small color="primary" @click="showConfirmation = true;">Submit</v-btn>
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
      <v-dialog
      v-model="showConfirmation"
      width="500"
      >
      <v-card>
        <v-card-title>
        Confirmation
        </v-card-title>

        <v-card-text>
        Are you sure you want to re-run the analysis job?
        The previous results will be overwritten.
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
            text
            @click="() => {showConfirmation = false}"
        >
            Cancel
        </v-btn>
        <v-btn
            color="primary"
            text
            @click="() => {methods.submitParams(); showConfirmation = false;}"
        >
            Yes, Rerun
        </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    </div>

</template>

<style>
  .justifyAround {
    display: flex;
    justify-content: space-around;
  }
</style>
