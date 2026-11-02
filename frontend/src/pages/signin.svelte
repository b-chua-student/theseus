<script>
  import AuthLayout from '../components/auth/AuthLayout.svelte';
  import { signIn } from '../lib/api/auth.js';
  let { onsuccess, onswitch } = $props();
  let name = $state(''), email = $state(''), password = $state(''), confirm = $state('');
  let busy = $state(false), error = $state('');
  async function submit(event) {
    event.preventDefault(); error = '';
    
    busy = true;
    try { const user = await signIn({ name, email, password }); password = ''; confirm = ''; onsuccess?.(user); }
    catch (e) { error = e.message || 'Unable to continue. Please retry.'; }
    finally { busy = false; }
  }
</script>
<AuthLayout title="Welcome back" subtitle="A focused space for your manuscripts.">
  <form onsubmit={submit}>
    
    <label>Email<input type="email" bind:value={email} required autocomplete="email" /></label>
    <label>Password<input type="password" bind:value={password} required  autocomplete="current-password" /></label>
    
    {#if error}<p class="error" role="alert">{error}</p>{/if}
    <button type="submit" disabled={busy}>{busy ? 'Please wait…' : 'Sign In to Theseus'}</button>
  </form>
  <p class="switch-row"><button class="switch" type="button" onclick={onswitch}>Sign Up<span aria-hidden="true">↗</span></button></p>
</AuthLayout>
