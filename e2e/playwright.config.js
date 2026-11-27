import { defineConfig } from '@playwright/test'

export default defineConfig({
  use: { baseURL: 'https://127.0.0.1:5173', ignoreHTTPSErrors: true },
  webServer: {
    cwd: '../frontend',
    command: 'npm run build && python ../e2e/openauth_server.py',
    url: 'https://127.0.0.1:5173/api/health',
    ignoreHTTPSErrors: true,
  },
})
