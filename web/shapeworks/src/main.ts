import * as Sentry from '@sentry/vue';
import Vue from 'vue';
import '@/plugins/composition';
import App from './App.vue';
import router from './router/routes';
import vuetify from './plugins/vuetify';
import { restoreLogin } from './api/auth';


Sentry.init({
  Vue,
  dsn: process.env.VUE_APP_SENTRY_DSN,
});

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
