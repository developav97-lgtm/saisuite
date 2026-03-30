export const environment = {
  production: true,
  apiUrl: 'https://api.saicloud.com/api/v1',
  apiBaseUrl: '',
  wsUrl: 'wss://api.saicloud.com',
  jwtTokenKey: 'saicloud_access_token',
  jwtRefreshTokenKey: 'saicloud_refresh_token',
  n8n: {
    webhookUrl: 'https://n8n.saicloud.com/webhook',
  },
  features: {
    enableDarkMode: true,
    enableNotifications: true,
  },
};
