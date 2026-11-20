import { randomUUID } from 'node:crypto'
import { test, expect } from '@playwright/test'

test('register, sign out, and sign back in', { tag: '@end-to-end' }, async ({ page }) => {
  const email = `reader-${randomUUID()}@example.com`
  const password = randomUUID()
  await page.goto('/')
  await page.getByRole('button', { name: 'Sign Up', exact: true }).click()
  await page.getByLabel('Name', { exact: true }).fill('Test Reader')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByLabel('Confirm password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Create Account', exact: true }).click()
  const account = page.getByRole('button', { name: 'Account', exact: true })
  await account.click()
  await page.getByRole('button', { name: 'Sign Out', exact: true }).click()
  await page.getByRole('button', { name: 'Sign In', exact: true }).click()
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign In to Theseus', exact: true }).click()
  await expect(account).toBeVisible()
  await page.reload()
  await expect(account).toBeVisible()
})
