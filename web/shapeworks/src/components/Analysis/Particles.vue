<script lang="ts">
import _ from 'lodash';
import {
  goodBadAngles,
  showGoodBadParticlesMode,
  goodBadMaxAngle,
} from '@/store';

export default {
    name: "Particles",
    setup() {

      function changeMaxAngle(angle: string) {
        if (parseFloat(angle)) {
          goodBadMaxAngle.value = parseFloat(angle);
        }
      }

      return {
        changeMaxAngle: _.debounce(changeMaxAngle, 1000),
        showGoodBadParticlesMode,
        goodBadAngles,
        goodBadMaxAngle,
      };
    },
};
</script>

<template>
    <div disabled="!goodBadAngles.value">
        <v-row justify="center">
          <v-switch
              class="mt-0 mb-8 pt-0"
              v-model="showGoodBadParticlesMode"
              label="Show Good/Bad Particles"
              hide-details
          ></v-switch>
        </v-row>
        <v-text-field
            :value="goodBadMaxAngle"
            type="number"
            step="1.0"
            min="1.0"
            max="360.0"
            label="Max Angle"
            hide-details
            @input="changeMaxAngle"
        />
    </div>
</template>
