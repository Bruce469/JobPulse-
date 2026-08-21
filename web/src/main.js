import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Jobs from './views/Jobs.vue'
import Predict from './views/Predict.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/jobs', name: 'jobs', component: Jobs },
    { path: '/predict', name: 'predict', component: Predict },
  ],
})

createApp(App).use(router).mount('#app')
