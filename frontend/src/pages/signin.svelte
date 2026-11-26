<script>
  import AuthLayout from '../components/auth/AuthLayout.svelte';
  import { onMount } from 'svelte';
  import { signIn, providerSettings } from '../lib/api/auth.js';
  let { onsuccess, onswitch } = $props();
  let email = $state(''), password = $state('');
  let busy = $state(false), error = $state('');
  let passwordError = $state('');
  let googleEnabled = $state(false);
  let loadingProviders = $state(true);
  let unavailable = $state('');
  const query = new URLSearchParams(location.search);
  const messages = {
    cancelled: 'Sign-in was cancelled. Please try again.',
    provider: "We couldn't sign you in with Google. Please try again.",
    email: 'We could not get an email address from your provider.',
    existing: 'Sign in using your existing method or password, then link your provider from Account.',
    unavailable: 'This account is unavailable. Please contact support.',
    timeout: 'Sign-in timed out. Please try again.',
    invalid: "We couldn't complete sign-in. Please try again.",
  };
  function startGoogle() {
    if (!googleEnabled) {
      unavailable = 'Google sign-in is unavailable.';
      error = '';
      return;
    }
    const destination = query.get('return_to') || location.pathname;
    location.assign('/api/auth/oauth/google/start?return_to=' + encodeURIComponent(destination));
  }
  async function loadProviders() {
    loadingProviders = true;
    unavailable = '';
    try {
      const settings = await providerSettings();
      googleEnabled = settings.providers.includes('google');
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
<AuthLayout title="Welcome back" subtitle="A focused space for your manuscripts.">
  <div class="provider-choices">
    <button type="button" disabled={loadingProviders} onclick={startGoogle}>Continue with Google</button>
    {#if unavailable}<p class="error" role="alert">{unavailable}</p>{/if}
  </div>
  {#if error}
    <div class="provider-notice">
      <p role="alert">{error}</p>
      <button type="button" onclick={() => googleEnabled ? startGoogle() : loadProviders()}>Try again</button>
    </div>
  {/if}
  <form onsubmit={submit}>
    
    <label>Email<input type="email" bind:value={email} required autocomplete="email" /></label>
    <label>Password<input type="password" bind:value={password} required  autocomplete="current-password" /></label>
    
    {#if passwordError}<p class="error" role="alert">{passwordError}</p>{/if}
    <button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign In to Theseus'}</button>
  </form>
  <p class="switch-row"><button class="switch" type="button" onclick={onswitch}>Sign Up<span aria-hidden="true">↗</span></button></p>
</AuthLayout>

<style>
  .provider-choices { display: grid; gap: 8px; margin-bottom: 16px; }
  .provider-choices button { padding: 9px 12px; border: 1px solid #cbd4ce; border-radius: 6px; background: white; color: var(--text-h); font: inherit; font-size: 12px; font-weight: 600; cursor: pointer; }
  .provider-choices button:hover { background: #f4f6f4; }
  .provider-notice { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 0 16px; padding: 10px 12px; background: #f7f4ee; border-radius: 6px; }
  .provider-notice p { margin: 0; color: #594a38; font-size: 12px; line-height: 1.45; }
  .provider-notice button { flex: none; border: 0; background: transparent; padding: 4px; color: #305447; font: inherit; font-size: 12px; font-weight: 600; text-decoration: underline; text-underline-offset: 3px; cursor: pointer; }
</style>
