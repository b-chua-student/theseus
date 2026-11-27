import { render, screen, fireEvent } from '@testing-library/svelte'
import { vi, expect, test } from 'vitest'
import SignIn from './signin.svelte'
import { providerSettings } from '../lib/api/auth.js'

vi.mock('../lib/api/auth.js', () => ({ providerSettings: vi.fn(), signIn: vi.fn() }))

test('S-029 explains unavailable Google on the sign-in page', async () => {
  const name = 'Google'
  vi.mocked(providerSettings).mockResolvedValue({ providers: [] })
  render(SignIn)
  const choice = await screen.findByRole('button', { name: 'Continue with ' + name })
  await fireEvent.click(choice)
  expect(await screen.findByRole('alert')).toHaveTextContent(name + ' sign-in is unavailable.')
  expect(choice).toBeVisible()
  expect(screen.queryByRole('button', { name: 'Continue with Microsoft' })).toBeNull()
  expect(screen.getByLabelText('Email')).toBeVisible()
})
