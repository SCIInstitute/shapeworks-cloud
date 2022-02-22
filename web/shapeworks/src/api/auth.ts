import axios from 'axios';
import OauthClient from '@girder/oauth-client';


export const apiClient = axios.create({
  baseURL: `${process.env.VUE_APP_API_ROOT}api/v1/`,
});
export const oauthClient = new OauthClient(
  process.env.VUE_APP_OAUTH_API_ROOT,
  process.env.VUE_APP_OAUTH_CLIENT_ID,
);

export async function restoreLogin() {
  if (!oauthClient) {
    return;
  }
  await oauthClient.maybeRestoreLogin();
}

apiClient.interceptors.request.use((config) => ({
  ...config,
  headers: {
    ...oauthClient?.authHeaders,
    ...config.headers,
  },
}));

export const logout = async () => {
  await oauthClient.logout();
  // TODO: clear cookies and local storage, which maintain csrftoken and sessionid
}
