<script lang="ts">
import { computed } from 'vue'
import { logout, oauthClient } from '@/api/auth';
import { allDatasets, loadingState, projectSortOption, projectSortAscending, selectedDataset, selectedProject, projectFilters, SORT_OPTION } from '@/store';
import FilterSearch from './FilterSearch.vue';
import router from '@/router';
import { getDatasets } from '@/api/rest';


export default {
    components: {
      FilterSearch
    },
    setup() {
      const params = computed(() => ({
        dataset: selectedDataset.value?.id,
        project: selectedProject.value?.id
      }))

      const ascendingLabel = computed(() => {
        return projectSortOption.value !== 'modified' ? "A to Z" : "Oldest"
      })

      async function logInOrOut() {
          if (oauthClient.isLoggedIn) {
            await logout();
            window.location.reload();
          } else {
            oauthClient.redirectToLogin();
          }
      }

      async function navigateToHome() {
        selectedDataset.value = undefined
        selectedProject.value = undefined
        if (router.currentRoute.path !== '/') {
          router.push('/')
        }
        loadingState.value = true;
        allDatasets.value = (await getDatasets(undefined)).sort((a, b) => {
            if(a.created < b.created) return 1;
            if(a.created > b.created) return -1;
            return 0;
        });
        loadingState.value = false;
      }

      return {
          oauthClient,
          params,
          logInOrOut,
          selectedDataset,
          selectedProject,
          navigateToHome,
          projectSortOption,
          projectSortAscending,
          ascendingLabel,
          projectFilters,
          SORT_OPTION,
          router,
      }
    }
}
</script>

<template>
  <v-app-bar app height="50px">
    <div class="d-flex align-center px-5" @click="navigateToHome">
      <v-img
        alt="ShapeWorks Logo"
        src="favicon.ico"
        transition="scale-transition"
        width="55px"
      />
      <v-toolbar-title class="text-h6">ShapeWorks</v-toolbar-title>
    </div>
    <v-spacer />
    <filter-search v-if="!(selectedDataset && selectedProject) && !(router.currentRoute.params.dataset && router.currentRoute.params.project)"/>
    <v-menu offset-y :close-on-content-click="false">
      <template v-slot:activator="{ on, attrs }">
        <v-btn
          class="ma-5"
          v-if="!(selectedDataset && selectedProject) && !(router.currentRoute.params.dataset && router.currentRoute.params.project)"
          hover
          icon
          v-bind="attrs"
          v-on="on"
        >
          <v-icon>
            mdi-filter-variant
          </v-icon>
        </v-btn>
      </template>
      <v-card>
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-header>Sort</v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card-text>
                <div class="flex">
                  <v-select
                    v-model="projectSortOption"
                    :items="Object.values(SORT_OPTION)"
                    label="Sort by"
                  />
                  <v-switch
                    v-model="projectSortAscending"
                    :label="ascendingLabel"
                  />
                </div>
              </v-card-text>
            </v-expansion-panel-content>
          </v-expansion-panel>
          <v-expansion-panel>
            <v-expansion-panel-header>Filter</v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card-text>
                <v-switch
                  v-model="projectFilters.private"
                  label="Hide private projects"
                />
                <v-switch
                  v-model="projectFilters.readonly"
                  label="Hide read only projects"
                />
              </v-card-text>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card>
    </v-menu>
    <v-spacer />
    <v-btn
      v-if="oauthClient.isLoggedIn"
      text
      @click="logInOrOut"
    >
      Logout
    </v-btn>
  </v-app-bar>
</template>

<style>
.router-link-active {
  color: white!important;
  text-decoration: none!important;
}
</style>
