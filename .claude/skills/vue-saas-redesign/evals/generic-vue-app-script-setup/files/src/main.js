import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Contacts from './views/Contacts.vue'
import Deals from './views/Deals.vue'
import Tasks from './views/Tasks.vue'
import Settings from './views/Settings.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Contacts },
    { path: '/deals', component: Deals },
    { path: '/tasks', component: Tasks },
    { path: '/settings', component: Settings }
  ]
})
createApp(App).use(router).mount('#app')
