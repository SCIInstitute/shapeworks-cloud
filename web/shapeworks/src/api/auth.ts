import axios from 'axios';
import OauthClient from '@girder/oauth-client';


export const axiosInstance = axios.create({
  baseURL: `${process.env.VUE_APP_API_ROOT}api`,
});
export const oauthClient = new OauthClient(
  process.env.VUE_APP_OAUTH_API_ROOT,
  process.env.VUE_APP_OAUTH_CLIENT_ID,
);

export async function restoreLogin() {
  if (!oauthClient) {
    return;
  }
  console.log('maybe restore', oauthClient)
  await oauthClient.maybeRestoreLogin();
}

axiosInstance.interceptors.request.use((config) => ({
  ...config,
  headers: {
    ...oauthClient?.authHeaders,
    ...config.headers,
  },
}));
