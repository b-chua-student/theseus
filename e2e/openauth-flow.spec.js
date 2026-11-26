import { randomUUID } from 'node:crypto'
import { test, expect } from '@playwright/test'

const email = () => randomUUID() + '@example.com'
const button = (page, name) => page.getByRole('button', { name, exact: true })
async function consent(page, address) {
  await expect(page.getByRole('heading', { name: 'Authorize Theseus' })).toBeVisible()
  await page.getByLabel('Email').fill(address)
  await button(page, 'Continue').click()
}
async function login(page, address, provider = 'Google') {
  await button(page, 'Continue with ' + provider).click()
  await consent(page, address)
}
async function logout(page) {
  await button(page, 'Account').click()
  await button(page, 'Sign Out').click()
}
const me = async page => (await page.request.get('/api/auth/me')).json()

test('S-008 S-020 S-021 S-022 S-025 restore the workspace and session securely', async ({ page, context }) => {
  const address = email()
  await page.goto('/')
  await login(page, address)
  const original = await me(page)
  await logout(page)
  await expect(button(page, 'Continue with ' + address)).toBeVisible()
  await page.goto('/workspace')
  await button(page, 'Continue with ' + address).click()
  await expect(page.getByRole('heading', { name: 'Research Workspace' })).toBeVisible()
  await page.reload()
  expect((await me(page)).id).toBe(original.id)
  const cookie = (await context.cookies()).find(c => c.name === 'session')
  expect(cookie).toMatchObject({ secure: true, httpOnly: true, sameSite: 'Lax' })
  const data = await page.evaluate(() => JSON.stringify([location.href, document.cookie,
    document.body.innerText, localStorage, sessionStorage, performance.getEntriesByType('resource').map(e => e.name)]))
  const audit = await page.request.post('https://127.0.0.1:5119/check-exposure', { data })
  expect(await audit.json()).toEqual({ issued: true, exposed: false })
  await button(page, 'Account').click()
  await page.getByLabel('Display name').fill('Alex')
  await button(page, 'Save').click()
  await expect(page.getByRole('status')).toHaveText('Name saved.')
  await page.reload()
  await button(page, 'Account').click()
  await expect(page.getByLabel('Display name')).toHaveValue('Alex')
  await button(page, 'Sign Out').click()
  await expect(button(page, 'Continue with ' + address)).toBeVisible()
  expect((await page.request.get('/api/auth/me')).status()).toBe(401)
  await page.goto('/workspace')
  await expect(button(page, 'Continue with ' + address)).toBeVisible()
})

for (const destination of ['https://example.org/profile', '//example.org/profile', '/removed']) {
  test('S-009 S-026 home fallback for ' + destination, async ({ page }) => {
    await page.goto('/?return_to=' + encodeURIComponent(destination))
    await login(page, email())
    await expect(page).toHaveURL('https://127.0.0.1:5173/')
    await expect(button(page, 'Account')).toBeVisible()
  })
}

test('S-017 interrupted consent can restart with Google or use a password', async ({ page }) => {
  await page.goto('/')
  await button(page, 'Continue with Google').click()
  await page.goto('/')
  await expect(page.getByRole('alert')).toHaveText('Sign-in wasn’t completed')
  await expect(page.getByLabel('Password')).toBeVisible()
  await login(page, email())
  await expect(button(page, 'Account')).toBeVisible()
})

test('S-024 S-033 explicitly link Google after password authentication', async ({ page }) => {
  const address = email()
  const response = await page.request.post('/api/auth/register', {
    data: { email: address, display_name: 'Password reader', password: 'test-password' },
  })
  const original = await response.json()
  await page.request.post('/api/auth/logout')
  await page.goto('/')
  await login(page, address)
  await expect(page.getByRole('alert')).toContainText('existing method')
  await expect(button(page, 'Try again')).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill(address)
  await page.getByLabel('Password', { exact: true }).fill('test-password')
  await button(page, 'Sign In to Theseus').click()
  await button(page, 'Account').click()
  await button(page, 'Link Google').click()
  await consent(page, address)
  await page.reload()
  await button(page, 'Account').click()
  await expect(page.getByText('Google connected', { exact: true })).toBeVisible()
  await expect(button(page, 'Link Google')).toHaveCount(0)
  await button(page, 'Account').click()
  await logout(page)
  await login(page, address)
  await expect(button(page, 'Account')).toBeVisible()
  expect((await me(page)).id).toBe(original.id)
})

for (const reachedServer of [true, false]) {
  test('S-022 ambiguous logout, reached server ' + reachedServer, async ({ page }) => {
    await page.goto('/')
    const address = email()
    await login(page, address)
    await page.route('**/api/auth/logout', async route => {
      if (reachedServer) await page.request.post('/api/auth/logout')
      await route.abort()
    })
    await logout(page)
    if (reachedServer) {
      await expect(button(page, 'Continue with ' + address)).toBeVisible()
    } else {
      await expect(page.getByRole('alert')).toContainText('Could not confirm sign-out')
      expect((await page.request.get('/api/auth/me')).status()).toBe(200)
    }
  })
}

test('Two independent callbacks resolve to one account', async ({ browser }) => {
  const contexts = await Promise.all([browser.newContext({ ignoreHTTPSErrors: true }), browser.newContext({ ignoreHTTPSErrors: true })])
  try {
    const address = email()
    const pages = await Promise.all(contexts.map(ctx => ctx.newPage()))
    await Promise.all(pages.map(page => page.goto('https://127.0.0.1:5173')))
    await Promise.all(pages.map(page => login(page, address)))
    const users = await Promise.all(pages.map(async page => {
      await expect(button(page, 'Account')).toBeVisible()
      return page.evaluate(async () => (await fetch('/api/auth/me')).json())
    }))
    expect(users[0].id).toBeTruthy()
    expect(users[1].id).toBe(users[0].id)
  } finally {
    await Promise.all(contexts.map(ctx => ctx.close()))
  }
})

test('S-022 unknown session after a failed logout can be retried', async ({ page }) => {
  await page.goto('/')
  const address = email()
  await login(page, address)
  await expect(button(page, 'Account')).toBeVisible()
  await page.route('**/api/auth/logout', route => route.abort())
  await page.route('**/api/auth/me', route => route.abort())
  await logout(page)
  await expect(page.getByRole('alert')).toContainText('Could not confirm sign-out')
  await page.unroute('**/api/auth/logout')
  await page.unroute('**/api/auth/me')
  await button(page, 'Try again').click()
  await expect(button(page, 'Continue with ' + address)).toBeVisible()
})

for (const [code, message] of Object.entries({
  cancelled: 'Sign-in was cancelled. Please try again.',
  provider: "We couldn't sign you in with Google. Please try again.",
  email: 'We could not get an email address from your provider.',
  unavailable: 'This account is unavailable. Please contact support.',
  timeout: 'This sign-in request expired.',
  connection: 'Theseus could not reach Google. Please try again.',
  invalid: "We couldn't complete sign-in. Please try again.",
})) {
  test('S-013–S-019 displays callback error ' + code, async ({ page }) => {
    await page.goto('/?auth_error=' + code + '&provider=google')
    await expect(page.getByRole('alert')).toHaveText(message)
    await expect(button(page, code === 'timeout' ? 'Restart Google sign-in' : 'Try again')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
  })
}

test('S-030 S-031 expired request starts a fresh Google flow', async ({ page }) => {
  await page.goto('/?auth_error=timeout&provider=google')
  await expect(page.getByText('New to Theseus? Your first Google sign-in creates your account.')).toHaveCount(0)
  await expect(button(page, 'Sign Up')).toBeVisible()
  await button(page, 'Restart Google sign-in').click()
  await consent(page, email())
  await expect(button(page, 'Account')).toBeVisible()
})

for (const reusable of [true, false]) {
  test('S-034 S-035 S-036 S-037 returning Google sign-in, reusable approval ' + reusable, async ({ page, context }) => {
    const address = email()
    await page.goto('/')
    await login(page, address)
    await expect(button(page, 'Account')).toBeVisible()
    const original = await me(page)
    await logout(page)
    await expect(button(page, 'Continue with ' + address)).toBeVisible()
    expect((await page.request.get('/api/auth/me')).status()).toBe(401)
    if (!reusable) await context.clearCookies({ name: 'fixture_grant' })

    const prompts = []
    page.on('request', req => {
      const url = new URL(req.url())
      if (url.pathname === '/authorize' && req.method() === 'GET') prompts.push(url.searchParams.get('prompt'))
    })
    await page.goto('/workspace')
    await button(page, 'Continue with ' + address).click()
    if (!reusable) {
      await expect(page.getByRole('heading', { name: 'Authorize Theseus' })).toBeVisible()
      expect((await page.request.get('/api/auth/me')).status()).toBe(401)
      await consent(page, address)
    }
    await expect(page.getByRole('heading', { name: 'Research Workspace' })).toBeVisible()
    expect((await me(page)).id).toBe(original.id)
    expect(prompts).toEqual(reusable ? ['none'] : ['none', null])
  })
}

test('Returning users can explicitly choose a different Google account', async ({ page }) => {
  await page.goto('/')
  await login(page, email())
  await expect(button(page, 'Account')).toBeVisible()
  const original = await me(page)
  await logout(page)
  await button(page, 'Use another Google account').click()
  await expect(page).toHaveURL(/prompt=select_account/)
  const nextAddress = email()
  await consent(page, nextAddress)
  await expect(button(page, 'Account')).toBeVisible()
  expect((await me(page)).id).not.toBe(original.id)
  await logout(page)
  await expect(button(page, 'Continue with ' + nextAddress)).toBeVisible()
})
