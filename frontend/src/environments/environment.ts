export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  apiBaseUrl: 'http://localhost:8000',
  jwtTokenKey: 'saicloud_access_token',
  jwtRefreshTokenKey: 'saicloud_refresh_token',
  n8n: {
    webhookUrl: 'http://localhost:5678/webhook',
  },
  features: {
    enableDarkMode: true,
    enableNotifications: true,
  },
};
