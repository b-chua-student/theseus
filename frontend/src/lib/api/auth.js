// DEMO ONLY: no identity verification. Passwords are never stored or sent.
// TODO(API): Replace these implementations with agreed authentication endpoints.
// Preserve the returned user shape: { name, email }. Use server sessions later.
const key = 'theseus.demo.session';
export function getSession() {
  try { return JSON.parse(sessionStorage.getItem(key) || 'null'); } catch { return null; }
}
export async function signIn({ email, password }) {
  if (!email.trim() || !password) throw new Error('Enter your email and password.');
  const user = { name: email.trim().split('@')[0], email: email.trim() };
  sessionStorage.setItem(key, JSON.stringify(user));
  return user;
}
export async function signUp({ name, email, password }) {
  if (!name.trim() || !email.trim() || password.length < 8) throw new Error('Complete all fields. Use at least 8 password characters.');
  const user = { name: name.trim(), email: email.trim() };
  sessionStorage.setItem(key, JSON.stringify(user));
  return user;
}
export async function signOut() { sessionStorage.removeItem(key); }
