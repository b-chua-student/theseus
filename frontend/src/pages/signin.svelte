<script>
  import AuthLayout from '../components/auth/AuthLayout.svelte';
  import { onMount } from 'svelte';
  import { signIn, providerSettings } from '../lib/api/auth.js';
  let { onsuccess, onswitch } = $props();
  let email = $state(''), password = $state('');
  let busy = $state(false), error = $state('');
  let passwordError = $state('');
  let googleEnabled = $state(false);
  let rememberedEmail = $state('');
  let returningGoogleUser = $state(false);
  let loadingProviders = $state(true);
  let unavailable = $state('');
  const query = new URLSearchParams(location.search);
  const messages = {
    cancelled: 'Sign-in was cancelled. Please try again.',
    provider: "We couldn't sign you in with Google. Please try again.",
    email: 'We could not get an email address from your provider.',
    existing: 'Sign in using your existing method or password, then link your provider from Account.',
    unavailable: 'This account is unavailable. Please contact support.',
    timeout: 'This sign-in request expired.',
    connection: 'Theseus could not reach Google. Please try again.',
    invalid: "We couldn't complete sign-in. Please try again.",
  };
  function startGoogle(chooseAccount = false) {
    if (!googleEnabled) {
      unavailable = 'Google sign-in is unavailable.';
      error = '';
      return;
    }
    const destination = query.get('return_to') || location.pathname;
    const params = new URLSearchParams(chooseAccount
      ? { return_to: destination, choose_account: '1' }
      : { return_to: destination });
    location.assign('/api/auth/oauth/google/start?' + params);
  }
  async function loadProviders() {
    loadingProviders = true;
    unavailable = '';
    try {
      const settings = await providerSettings();
      googleEnabled = settings.providers.includes('google');
      rememberedEmail = settings.remembered_google_email || '';
      returningGoogleUser = settings.returning_google_user === true;
      error = settings.interrupted ? 'Sign-in wasn’t completed' : (messages[query.get('auth_error')] || '');
    } catch (e) { googleEnabled = false; error = e.message; }
    finally { loadingProviders = false; }
  }
  onMount(() => {
    loadProviders();
    const onPageShow = event => { if (event.persisted) loadProviders(); };
    window.addEventListener('pageshow', onPageShow);
    return () => window.removeEventListener('pageshow', onPageShow);
  });
  async function submit(event) {
    event.preventDefault(); error = ''; unavailable = ''; passwordError = '';

    busy = true;
    try { const user = await signIn({ email, password }); password = ''; onsuccess?.(user); }
    catch (e) { passwordError = e.message || 'Unable to continue. Please retry.'; }
    finally { busy = false; }
  }
</script>
<AuthLayout mode="signin" {onswitch} title="Welcome back" subtitle="A focused space for your manuscripts.">
  <form onsubmit={submit}>

    <label>Email<input type="email" bind:value={email} required autocomplete="email" /></label>
    <label>Password<input type="password" bind:value={password} required  autocomplete="current-password" /></label>

    {#if passwordError}<p class="error" role="alert">{passwordError}</p>{/if}
    <button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign In to Theseus'}</button>
  </form>
  <div class="provider-choices">
    <div class="divider" aria-hidden="true">or</div>
    <button class="google-button" type="button" disabled={loadingProviders} onclick={() => startGoogle()}>
      <svg viewBox="0 0 48 48" width="20" height="20" aria-hidden="true">
        <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
        <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
        <path fill="#FBBC05" d="M10.53 28.59a14.4 14.4 0 0 1 0-9.18l-7.97-6.19a23.99 23.99 0 0 0 0 21.56l7.97-6.19z"/>
        <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.91-5.8l-7.73-6c-2.15 1.45-4.92 2.3-8.18 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.97 6.19C6.51 42.62 14.62 48 24 48z"/>
      </svg>
      <span>Continue with {googleEnabled && rememberedEmail ? rememberedEmail : 'Google'}</span>
    </button>
    {#if returningGoogleUser && googleEnabled}
      <button type="button" onclick={() => startGoogle(true)}>Use another Google account</button>
    {/if}
    {#if unavailable}<p class="error" role="alert">{unavailable}</p>{/if}
  </div>
  {#if error}
    <div class="provider-notice">
      <p role="alert">{error}</p>
      <button type="button" onclick={() => googleEnabled ? startGoogle() : loadProviders()}>{error === messages.timeout ? 'Restart Google sign-in' : 'Try again'}</button>
    </div>
  {/if}
</AuthLayout>

<style>
  .provider-choices { display: grid; gap: 14px; margin: 16px 0 0; }
  .provider-choices button { padding: 9px 12px; border: 1px solid #cbd4ce; border-radius: 6px; background: white; color: var(--text-h); font: inherit; font-size: 12px; font-weight: 600; cursor: pointer; }
  .provider-choices button:hover { background: #f4f6f4; }
  .divider { display: flex; align-items: center; gap: 10px; color: #626862; font-size: 12px; }
  .divider::before, .divider::after { content: ''; flex: 1; border-top: 1px solid #dce1dc; }
  .provider-choices .google-button { display: flex; align-items: center; justify-content: center; gap: 10px; min-height: 50px; border-color: #747775; color: #1f1f1f; font-size: 14px; font-weight: 500; }
  .google-button svg { flex-shrink: 0; }
  .google-button span { overflow-wrap: anywhere; }
  .provider-notice { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 0 16px; padding: 10px 12px; background: #f7f4ee; border-radius: 6px; }
  .provider-notice p { margin: 0; color: #594a38; font-size: 12px; line-height: 1.45; }
  .provider-notice button { flex: none; border: 0; background: transparent; padding: 4px; color: #305447; font: inherit; font-size: 12px; font-weight: 600; text-decoration: underline; text-underline-offset: 3px; cursor: pointer; }
</style>
