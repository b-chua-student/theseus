<script>
  import AuthLayout from '../components/auth/AuthLayout.svelte';
  import { signUp } from '../lib/api/auth.js';
  let { onsuccess, onswitch } = $props();
  let name = $state(''), email = $state(''), password = $state(''), confirm = $state('');
  let busy = $state(false), error = $state('');
  async function submit(event) {
    event.preventDefault(); error = '';
    if (password !== confirm) { error = 'Passwords do not match.'; return; }
    busy = true;
    try { const user = await signUp({ name, email, password }); password = ''; confirm = ''; onsuccess?.(user); }
    catch (e) { error = e.message || 'Unable to continue. Please retry.'; }
    finally { busy = false; }
  }
</script>
<AuthLayout title="Create your account" subtitle="A focused space for your manuscripts.">
  <form onsubmit={submit}>
    <label>Name<input bind:value={name} required autocomplete="name" /></label>
    <label>Email<input type="email" bind:value={email} required autocomplete="email" /></label>
    <label>Password<input type="password" bind:value={password} required minlength="8" autocomplete="new-password" /></label>
    <label>Confirm password<input type="password" bind:value={confirm} required autocomplete="new-password" /></label>
    {#if error}<p class="error" role="alert">{error}</p>{/if}
    <button type="submit" disabled={busy}>{busy ? 'Creating account…' : 'Create Account'}</button>
  </form>
  <p class="switch-row"><button class="switch" type="button" onclick={onswitch}>Sign In<span aria-hidden="true">↗</span></button></p>
</AuthLayout>
