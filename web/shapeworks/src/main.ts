import Vue from 'vue';
import '@/plugins/composition';
import App from './App.vue';
import router from './router';
import vuetify from './plugins/vuetify';
import { restoreLogin } from './api/auth';


async function login() {
  return restoreLogin();
}

login().then(() => {
  new Vue({
    router,
    vuetify,
    render: (h) => h(App),
  }).$mount('#app');
});
