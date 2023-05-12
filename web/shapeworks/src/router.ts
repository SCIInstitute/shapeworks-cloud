import Vue from 'vue'
import VueRouter, { Route, RouteConfig } from 'vue-router'
import Main from './views/Main.vue'
import ProjectSelect from './views/ProjectSelect.vue'
import DatasetSelect from './views/DatasetSelect.vue'


Vue.use(VueRouter)

const castDatasetAndSubjectProps = (route: Route) => ({
  dataset: parseInt(route.params.dataset),
  project: parseInt(route.params.project),
});

const routes: Array<RouteConfig> = [
  {
    path: '/dataset/:dataset/project/:project',
    name: 'main',
    props: castDatasetAndSubjectProps,
    component: Main
  },
  {
    path: 'dataset/:dataset/search/:searchText',
    name: 'search',
    component: ProjectSelect,
  },
  {
    path: '/search/:searchText',
    name: 'search',
    component: DatasetSelect,
  },
  {
    path: '/dataset/:dataset',
    name: 'main',
    component: ProjectSelect
  },
  {
    path: '/',
    name: 'select',
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
