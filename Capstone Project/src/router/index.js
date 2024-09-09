import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import App from '../App.vue';

// Import views
import HomeView from '../views/HomeView.vue';

// Define routes
const routes = [
  {
    path: '/HomeView',
    name: 'Home Page',
    component: HomeView,
  },
];

// Create the router
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Create the app with the router
createApp(App).use(router).mount('#app');

export default router

