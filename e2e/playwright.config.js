import { defineConfig } from '@playwright/test'

export default defineConfig({
  use: { baseURL: 'http://127.0.0.1:5173' },
  webServer: [
    {
      cwd: '../backend',
      command: 'python -m flask --app api.app run --port 5000',
      url: 'http://127.0.0.1:5000/api/health',
    },
    {
      cwd: '../frontend',
      command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173',
    },
  ],
})
