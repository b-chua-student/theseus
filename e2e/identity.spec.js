import { randomUUID } from 'node:crypto'
import { test, expect } from '@playwright/test'

test('register, sign out, and sign back in', { tag: '@end-to-end' }, async ({ page }) => {
  const email = `reader-${randomUUID()}@example.com`
  const password = randomUUID()
  await page.goto('/')
  const register = /register|sign up|create account/i
  await page.getByRole('button', { name: register }).or(page.getByRole('link', { name: register })).click()
  await page.getByLabel(/display name/i).fill('Test Reader')
  await page.getByLabel(/email/i).fill(email)
  await page.getByLabel(/^password$/i).fill(password)
  await page.getByRole('button', { name: register }).click()
  const logout = page.getByRole('button', { name: /log out|sign out/i })
  await expect(logout).toBeVisible()
  await logout.click()
  await page.getByLabel(/email/i).fill(email)
  await page.getByLabel(/^password$/i).fill(password)
  await page.getByRole('button', { name: /sign in|log in/i }).click()
  await expect(logout).toBeVisible()
  await page.reload()
  await expect(logout).toBeVisible()
})
