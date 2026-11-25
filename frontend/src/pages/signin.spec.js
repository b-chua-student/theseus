import { render, screen, fireEvent } from '@testing-library/svelte'
import { vi, expect, test } from 'vitest'
import SignIn from './signin.svelte'
import { providerSettings } from '../lib/api/auth.js'

vi.mock('../lib/api/auth.js', () => ({ providerSettings: vi.fn(), signIn: vi.fn() }))

test.each(['Google', 'Microsoft'])('S-029 explains unavailable %s on the sign-in page', async name => {
  providerSettings.mockResolvedValue({ providers: [] })
  render(SignIn)
  const choice = await screen.findByRole('button', { name: 'Continue with ' + name })
  await fireEvent.click(choice)
  expect(await screen.findByRole('alert')).toHaveTextContent(name + ' sign-in is unavailable.')
  for (const provider of ['Google', 'Microsoft']) {
    expect(screen.getByRole('button', { name: 'Continue with ' + provider })).toBeVisible()
  }
  expect(screen.getByLabelText('Email')).toBeVisible()
})
