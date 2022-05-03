<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import {
    particleSize,
    layers,
    layersShown,
    orientationIndicator,
} from '../store';


export default defineComponent({
    setup(props, context) {
        orientationIndicator.value.setDefaultStyle({
            fontStyle: 'bold',
            fontFamily: 'Arial',
            fontColor: 'black',
            faceColor: '#ffffff',
            faceRotation: 0,
            edgeThickness: 0.1,
            edgeColor: 'black',
            resolution: 400,
        })

        const axisSystemOptions = [
            {
                text: 'XYZ',
                value: 'xyz',
                xPlus: '+X',
                xMinus: '-X',
                yPlus: '+Y',
                yMinus: '-Y',
                zPlus: '+Z',
                zMinus: '-Z',
            },
            {
                text: 'Medical',
                value: 'slp',
                xPlus: 'L',
                xMinus: 'R',
                yPlus: 'P',
                yMinus: 'A',
                zPlus: 'S',
                zMinus: 'I',
            }
        ]

        function changeAxisSystem(newSystemValue: string){
            const newSystem = axisSystemOptions.find(
                (system) => system.value == newSystemValue
            )
            if(newSystem){
                orientationIndicator.value.setXPlusFaceProperty({
                    text: newSystem.xPlus
                })
                orientationIndicator.value.setXMinusFaceProperty({
                    text: newSystem.xMinus
                })
                orientationIndicator.value.setYPlusFaceProperty({
                    text: newSystem.yPlus
                })
                orientationIndicator.value.setYMinusFaceProperty({
                    text: newSystem.yMinus
                })
                orientationIndicator.value.setZPlusFaceProperty({
                    text: newSystem.zPlus
                })
                orientationIndicator.value.setZMinusFaceProperty({
                    text: newSystem.zMinus
                })
                context.emit("change")
            }
        }

        return {
            particleSize,
            layersShown,
            layers,
            axisSystemOptions,
            changeAxisSystem,
        }
    }
})
</script>

<template>
    <div class="render-control-bar">
        <v-select
            v-model="layersShown"
            :items="layers"
            label="Layers shown"
            style="width: 500px"
            multiple
            small-chips
            item-text="name"
        >
            <template #selection="{ item, index }">
                <v-chip
                    close
                    @click:close="layersShown.splice(index, 1)"
                    :color="item.color"
                    :text-color="item.color === 'white' ? 'black' : 'white'"
                >
                    {{ item.name }}
                </v-chip>
            </template>
        </v-select>
        <v-text-field
            v-model.number="particleSize"
            v-if="layersShown.includes('Particles')"
            label="Particle Size"
            type="number"
            style="width: 80px"
            step="0.5"
            min="0.5"
            max="10"
            hide-details
        />
        <v-select
            :items="axisSystemOptions"
            value="xyz"
            @change="changeAxisSystem"
            label="Axis System"
            style="width: 150px"
        />
    </div>
</template>

<style scoped>
.render-control-bar {
    display: flex;
    width: 100%;
    height: 70px;
    justify-content: space-between;
}
.render-control-bar > * {
    flex-grow: 0;
}
</style>
