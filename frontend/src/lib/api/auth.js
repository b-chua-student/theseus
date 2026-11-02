const key = 'theseus.session';

export function getSession() {
  try { return JSON.parse(sessionStorage.getItem(key) || 'null'); } catch { return null; }
}

export async function signIn({ email, password }) {
  if (!email.trim() || !password) throw new Error('Enter your email and password.');
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.trim(), password }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || err.detail || 'Login failed.');
  }
  const user = await res.json();
  sessionStorage.setItem(key, JSON.stringify(user));
  return user;
}

export async function signUp({ name, email, password }) {
  if (!name.trim() || !email.trim() || password.length < 8) throw new Error('Complete all fields. Use at least 8 password characters.');
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: name.trim(), email: email.trim(), password }),
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || err.detail || 'Registration failed.');
  }
  const user = await res.json();
  sessionStorage.setItem(key, JSON.stringify(user));
  return user;
}

export async function signOut() { sessionStorage.removeItem(key); }
