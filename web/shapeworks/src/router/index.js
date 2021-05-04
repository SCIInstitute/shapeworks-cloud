import Vue from 'vue'
import VueRouter from 'vue-router'
import Data from '../views/Data'
import Groom from '../views/Groom'
import Optimize from '../views/Optimize'
import Analyze from '../views/Analyze'
import Demo from '../views/Demo'

Vue.use(VueRouter)

const routes = [
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
  }
]

const router = new VueRouter({
  routes
})

export default router
