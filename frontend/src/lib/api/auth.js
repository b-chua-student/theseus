import { apiFetch } from './http.js';

export async function getSession() {
  const response = await fetch('/api/auth/me', { credentials: 'same-origin', cache: 'no-store' });
  if (response.status === 401) return null;
  if (!response.ok) throw new Error('Could not check your session. Please try again.');
  return response.json();
}

export async function providerSettings() {
  return (await apiFetch('/api/auth/oauth/providers', { cache: 'no-store' }, 'Could not load sign-in options.')).json();
}
export async function signIn({ email, password }) {
  if (!email.trim() || !password) throw new Error('Enter your email and password.');
  const res = await apiFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim(), password }),
  }, 'Sign in failed. Please try again.');
  const user = await res.json();
  return user;
}

export async function signUp({ name, email, password }) {
  if (!name.trim() || !email.trim() || password.length < 8) throw new Error('Complete all fields. Use at least 8 password characters.');
  const res = await apiFetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: name.trim(), email: email.trim(), password }),
  }, 'Could not create your account. Please try again.');
  const user = await res.json();
  return user;
}

export async function signOut() {
  try {
    const response = await fetch('/api/auth/logout', { method: 'POST' });
    if (response.status === 204) return;
  } catch { /* The server may already have ended the session. */ }
  if (await getSession() === null) return;
  throw new Error('Could not confirm sign-out. Please try again.');
}
