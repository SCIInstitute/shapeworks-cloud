import Vue from 'vue'
import VueRouter, { Route, RouteConfig } from 'vue-router'
import Select from './views/Select.vue'
import Main from './views/Main.vue'

Vue.use(VueRouter)

const castDatasetAndSubjectProps = (route: Route) => ({
  dataset: parseInt(route.params.dataset),
  subject: parseInt(route.params.subject),
});

const routes: Array<RouteConfig> = [
  {
    path: '/dataset/:dataset',
    name: 'main',
    props: castDatasetAndSubjectProps,
    component: Main
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
