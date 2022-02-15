import Vue from 'vue'
import VueRouter, { RouteConfig } from 'vue-router'
import Select from '../views/Select.vue'
import Data from '../views/Data.vue'
import Groom from '../views/Groom.vue'
import Optimize from '../views/Optimize.vue'
import Analyze from '../views/Analyze.vue'
import Demo from '../views/Demo.vue'

Vue.use(VueRouter)

const routes: Array<RouteConfig> = [
  {
    path: '/data',
    name: 'data',
    component: Data
  },
  {
    path: '/groom',
    name: 'groom',
    component: Groom
  },
  {
    path: '/optimize',
    name: 'optimize',
    component: Optimize
  },
  {
    path: '/analyze',
    name: 'analyze',
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
