import Vue from 'vue'
import VueRouter, { Route, RouteConfig } from 'vue-router'
import Main from './views/Main.vue'
import ProjectSelect from './views/ProjectSelect.vue'
import DatasetSelect from './views/DatasetSelect.vue'


Vue.use(VueRouter)

const castDatasetAndSubjectProps = (route: Route) => ({
    dataset: (route.params.dataset) ? parseInt(route.params.dataset): undefined,
    project: (route.params.project) ? parseInt(route.params.project): undefined,
    searchText: route.params.searchText,
  });

const routes: Array<RouteConfig> = [
  {
    path: '/dataset/:dataset/project/:project',
    name: 'main',
    props: castDatasetAndSubjectProps,
    component: Main
  },
  {
    path: '/dataset/:dataset/search/:searchText',
    name: 'project-search',
    props: castDatasetAndSubjectProps,
    component: ProjectSelect,
  },
  {
    path: '/search/:searchText',
    name: 'dataset-search',
    props: castDatasetAndSubjectProps,
    component: DatasetSelect,
  },
  {
    path: '/dataset/:dataset',
    name: 'project-select',
    props: castDatasetAndSubjectProps,
    component: ProjectSelect
  },
  {
    path: '/',
    name: 'dataset-select',
    props: castDatasetAndSubjectProps,
    component: DatasetSelect,
  },
  {
    path: '*',
    redirect: '/',
  },
]

const router = new VueRouter({
  routes
})

export default router
