<script lang="ts">
  import { analysis, analysisFileShown, cacheAllComparisons, currentAnalysisFileParticles, meanAnalysisFileParticles } from '@/store';
import { AnalysisGroup } from '@/types';
import { Ref, computed, defineComponent, inject, ref, watch } from '@vue/composition-api';

import { AnalysisTabs } from './AnalysisTab.vue';
  
  export default defineComponent({
    props: {
      currentTab: String,
      openTab: Number,
    },
    setup(props) {
      const currGroup = ref<AnalysisGroup>();
      const groupRatio = ref(0.5);
      const groupDiff = ref(false);
      const groupSet = ref<string>();
      const currPairing = ref<{left: string, right: string}>({left:"", right:""});
      const prevPairing = ref<{left: string, right: string}>({left:"", right:""}); // stores the previously selected pairing

      const currentlyCaching: Ref | undefined = inject('currentlyCaching');
      const animate: Ref | undefined = inject('animate'); 

      let step = 0.1;
      let intervalId: number;

      const methods = {
        // determine if the currently selected group pairing is inverted
        // returns true if they are inverted, false if not
        pairingIsInverted(g: any) {
            return (g.group1 === currPairing.value.right && g.group2 === currPairing.value.left)
        },
        updateCurrGroup() {
            currGroup.value = analysis.value?.groups.find((g) => {
                if (g.name === groupSet.value) {
                    if ((g.group1 === currPairing.value.left && g.group2 === currPairing.value.right) 
                        || (g.group1 === currPairing.value.right && g.group2 === currPairing.value.left)) { // if the groups pairings match the selected pairings
                        if (!methods.pairingIsInverted(g))  { // in-order group pairings
                            if (g.ratio === groupRatio.value) {
                                return true;
                            }
                        } else if (methods.pairingIsInverted(g)) { // inverted group pairings
                            if (g.ratio === parseFloat((1 - groupRatio.value).toFixed(1))) { // floating point precision errors (https://en.wikipedia.org/wiki/Floating-point_arithmetic#Accuracy_problems)
                                return true;
                            }
                        }
                    }
                }
            })
        },
        setDefaultPairing() {
            // default left and right group selections: first and second item in groupSet pairings list
            if (groupSet.value !== undefined) {
                currPairing.value.left = groupPairings.value[groupSet.value][0];
                currPairing.value.right = groupPairings.value[groupSet.value][1];
                prevPairing.value = {left: currPairing.value.left, right: currPairing.value.right};
            }
        },
        // triggered on group pairing select change
        updateGroupSelections() {
            // if the new left and right groups are the same, flip the two values according to the previous selections
            if (currPairing.value.left === currPairing.value.right && groupSet.value !== undefined) {
                // set new non-changed side to opposite side in old pairing
                if (currPairing.value.left === prevPairing.value.left) {
                    currPairing.value.left = prevPairing.value.right;
                }
                if (currPairing.value.right === prevPairing.value.right) {
                    currPairing.value.right = prevPairing.value.left;
                }
            }   
            
            prevPairing.value.left = currPairing.value.left;
            prevPairing.value.right = currPairing.value.right;

            methods.updateGroupFileShown();
        },
        updateGroupFileShown() {
            let fileShown = undefined;
            let particles = undefined;
            methods.updateCurrGroup();

            if (props.currentTab === 'analyze' && analysis.value && currGroup.value){
                fileShown = currGroup.value.file;
                particles = currGroup.value.particles;
            }
            currentAnalysisFileParticles.value = particles;
            if (groupDiff.value) {
                meanAnalysisFileParticles.value = analysis.value?.groups.find((g) => {
                    if (g.name === groupSet.value) {
                      if (!methods.pairingIsInverted(g)) {
                        if (g.ratio === 1.0) return true;
                      } else if (methods.pairingIsInverted(g)) {
                        if (g.ratio === 0.0) return true;
                      }
                    }
                })?.particles // account for inverted-pairings
            } else {
                meanAnalysisFileParticles.value = analysis.value?.mean_particles;
            }

            analysisFileShown.value = fileShown;
        },
        async cacheAllGroupComparisons() {
            const allInPairing = analysis.value?.groups.filter((g) => {
                if (g.name === groupSet.value) { // if groupSet is same
                    if ((g.group1 === currPairing.value.left || g.group1 === currPairing.value.right) && (g.group2 === currPairing.value.left || g.group2 === currPairing.value.right))
                        return true;
                }
            })

            if (allInPairing !== undefined) {
                await cacheAllComparisons(allInPairing);
            }
        },
        animateSlider() {
            if (props.openTab === AnalysisTabs.Groups) { // Group tab animate
                if (groupRatio.value === 0) step = 0.1;
                if (groupRatio.value === 1) step = -0.1;
                groupRatio.value = parseFloat((groupRatio.value + step).toFixed(1));
            }
        },
        async triggerAnimate() {
            if (groupSet.value === undefined || animate == undefined) return;

            if (animate.value && currentlyCaching) {
                currentlyCaching.value = true;
                await methods.cacheAllGroupComparisons();
                currentlyCaching.value = false;
                intervalId = setInterval(methods.animateSlider, 500);
            }
            if (animate.value === false && intervalId) {
                clearInterval(intervalId);
            }
        }
      };
  
      const allGroupSets = computed(() => { 
          return analysis.value?.groups.map((g) => g.name); 
      })

      // get all possible unique group pairings
      const groupPairings = computed(() => {
            const g: { [name: string]: string[] } = {};
            analysis.value?.groups.map((group: AnalysisGroup) => {
                if (g[group.name] === undefined) g[group.name] = [];
                if (!g[group.name].includes(group.group1)) g[group.name].push(group.group1);
                if (!g[group.name].includes(group.group2)) g[group.name].push(group.group2);
            })
            return g;
        })

        watch(groupSet, () => {
            methods.setDefaultPairing(); 
            methods.updateGroupFileShown();
        })
        watch(currPairing.value, methods.updateGroupSelections)
        watch(groupRatio, methods.updateGroupFileShown)
        watch(groupDiff, methods.updateGroupFileShown)

        if (animate) {
            watch(animate, methods.triggerAnimate)
        }
        
      return {
        methods,
        groupRatio,
        groupDiff,
        groupSet,
        allGroupSets,
        groupPairings,
        currGroup,
        currPairing,
        animate,
        currentlyCaching
      };
    },
  });
</script>
  
<template>
    <div>
      <v-select
          label="Group Set"
          v-model="groupSet"
          :items="allGroupSets"
          item-text="set"
          item-value="set"
      />
      <v-divider></v-divider>
      <v-row 
          align="center" 
          justify="center"
      >
          <v-col>
              <v-select
                  v-model="currPairing.left"
                  :items="(currGroup && groupSet) ? groupPairings[groupSet] : ['']"
                  item-text="group1"
                  item-value="group1"
              />
          </v-col>
          <v-col>
              <v-slider
                  v-model="groupRatio"
                  min="0.0"
                  max="1.0"
                  step="0.1"
                  default="0.5"
                  show-ticks="always"
                  hide-details
                  :disabled="currGroup === undefined"
              ></v-slider>
          </v-col>
          <v-col>
              <v-select
                  v-model="currPairing.right"
                  :items="(currGroup && groupSet) ? groupPairings[groupSet] : ['']"
                  item-text="group2"
                  item-value="group2"
              />
          </v-col>
      </v-row>
      <v-row justify="center">
          <v-checkbox
              :disabled="currGroup === undefined"
              class="mt-0 mb-8 pt-0"
              v-model="animate"
              label="Animate"
              hide-details
          ></v-checkbox>
      </v-row>
      <v-card align="center" justify="center" class="ma-auto mb-3" :disabled="currGroup === undefined">
          <v-btn class="ms-4" color="grey darken-3" @click="() => { groupRatio = 0.0;}">Left Mean</v-btn>
          <v-btn-toggle class="ms-4" color="white"><v-btn color="grey darken-4" :disabled="animate || currentlyCaching" @click="() => groupDiff = !groupDiff">Diff --></v-btn></v-btn-toggle>
          <v-btn class="ms-4" color="grey darken-3" @click="() => { groupRatio = 1.0;}">Right Mean</v-btn>
      </v-card>
    </div>
</template>

<style>

</style>
  