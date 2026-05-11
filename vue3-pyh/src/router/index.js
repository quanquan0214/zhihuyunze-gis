import { createRouter, createWebHistory } from 'vue-router'

import Home from '@/views/layout/home.vue'
import Introduce from '@/views/layout/introduce.vue'
import Login from '@/views/login/login.vue'
import Pattern from '@/views/layout/pattern.vue'
import RSEI from '@/views/layout/RSEI.vue'
import Landcoverage from '@/views/sublayout/landcoverage.vue'
import Temperature from '@/views/sublayout/temperature.vue'
import Waterstatistics from '@/views/sublayout/waterstatistics.vue'
import Monitor from '@/views/layout/monitor.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      component: Home,
      redirect:"/introduce",
      children: [
        { path: "introduce", component: Introduce },
        { path: "waterstatistics", component: Waterstatistics },
        { path: "landcoverage", component: Landcoverage },
        { path: "temperature", component: Temperature },
        { path: "pattern", component: Pattern },
        { path: "rsei", component: RSEI },
        { path: "monitor", component: Monitor },
      ],
    },
    { path: "/login", component: Login },
  ],
})

export default router