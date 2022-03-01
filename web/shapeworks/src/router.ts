import Vue from 'vue'
import VueRouter, { Route, RouteConfig } from 'vue-router'
import Select from './views/Select.vue'
import Data from './views/Data.vue'
import Groom from './views/Groom.vue'
import Optimize from './views/Optimize.vue'
import Analyze from './views/Analyze.vue'
import Demo from './views/Demo.vue'

Vue.use(VueRouter)

const castDatasetAndSubjectProps = (route: Route) => ({
  dataset: parseInt(route.params.dataset),
  subject: parseInt(route.params.subject),
});

const routes: Array<RouteConfig> = [
  {
    path: '/dataset/:dataset/subject/:subject/data',
    name: 'data',
    props: castDatasetAndSubjectProps,
    component: Data
  },
  {
    path: '/dataset/:dataset/subject/:subject/groom',
    name: 'groom',
    props: castDatasetAndSubjectProps,
    component: Groom
  },
  {
    path: '/dataset/:dataset/subject/:subject/optimize',
    name: 'optimize',
    props: castDatasetAndSubjectProps,
    component: Optimize
  },
  {
    path: '/dataset/:dataset/subject/:subject/analyze',
    name: 'analyze',
    props: castDatasetAndSubjectProps,
    component: Analyze,
  },
  {
    path: '/demo',
    name: 'demo',
    component: Demo,
  },
  {
    path: '/',
    name: 'select',
    component: Select,
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
