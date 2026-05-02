import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('./views/HomePage.vue'),
  },
  {
    path: '/inspect/:name',
    name: 'inspect',
    component: () => import('./views/InspectPage.vue'),
  },
  {
    path: '/diff/:name',
    name: 'diff',
    component: () => import('./views/DiffPage.vue'),
  },
  {
    path: '/run/:id?',
    name: 'run',
    component: () => import('./views/RunPage.vue'),
  },
  {
    path: '/publish/:name',
    name: 'publish',
    component: () => import('./views/PublishPage.vue'),
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
