export const environment = {
  production: true,
  apiUrl: 'https://api.saicloud.com/api/v1',
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
