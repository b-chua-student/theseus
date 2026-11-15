import { svelte } from '@sveltejs/vite-plugin-svelte'
import { svelteTesting } from '@testing-library/svelte/vite'
import { defineConfig } from 'vitest/config'

// Component tests: `*.spec.js` (run by vitest). `*.test.js` stay on node:test.
export default defineConfig({
  plugins: [svelte(), svelteTesting()],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.spec.js'],
    setupFiles: ['./vitest.setup.js'],
  },
})
