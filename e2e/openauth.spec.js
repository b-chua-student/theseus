import { test as base, expect } from '@playwright/test'

const test = base.extend({
  signedOutPage: async ({ page }, use) => {
    await page.route('**/api/auth/oauth/providers', route =>
      route.fulfill({ json: { providers: ['google', 'microsoft'] } }))
    await page.goto('/')
    await use(page)
  },
})

test('S-001 shows both enabled provider choices', async ({ signedOutPage }) => {
  for (const name of ['Continue with Google', 'Continue with Microsoft']) {
    await expect(signedOutPage.getByRole('button', { name, exact: true })).toBeVisible()
  }
})

test('S-002 navigates to the selected provider start', async ({ signedOutPage }) => {
  await signedOutPage.route('**/api/auth/oauth/google/start*', route =>
    route.fulfill({ contentType: 'text/html', body: '<h1>Authorize Theseus</h1>' }))
  await signedOutPage.getByRole('button', { name: 'Continue with Google' }).click()
  await expect(signedOutPage.getByRole('heading', { name: 'Authorize Theseus' })).toBeVisible()
})
