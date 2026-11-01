<script>
  let { inEditor = false, documentTitle = '', manuscriptCount = 0, onworkspace } = $props();
  let profileOpen = $state(false);
  function closeProfile(event) { if (!event.target.closest?.('.profile-control')) profileOpen = false; }
</script>

<svelte:window onclick={closeProfile} onkeydown={event => { if (event.key === 'Escape') profileOpen = false; }} />
<header class="app-header" aria-label="Theseus navigation">
  <div class="navigation-left">
    <button type="button" class="brand" onclick={() => onworkspace?.()} aria-label="Theseus workspace"><span class="brand-mark"></span><span>THESEUS</span></button>
    <span class="nav-divider"></span>
    <nav class="breadcrumbs" aria-label="Workspace navigation">
      <button type="button" class="workspace-link" class:breadcrumb-active={!inEditor} onclick={() => onworkspace?.()}><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 7V5h7l2 3h9v13H3Z" /></svg>Workspace</button>
      <span class="chevron">›</span><span class="current" class:breadcrumb-active={inEditor} aria-current="page" title={inEditor ? String(documentTitle) : 'Manuscripts'}>{inEditor ? 'Manuscript Editor' : 'Manuscripts'}</span>
      {#if !inEditor}<span class="count">{manuscriptCount}</span>{/if}
    </nav>
  </div>
  <div class="profile-control">
    <button type="button" class="profile-button" onclick={() => profileOpen = !profileOpen} aria-expanded={profileOpen} aria-controls="account-menu"><span class="avatar" aria-hidden="true"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M5 22v-3a7 7 0 0 1 14 0v3"/></svg></span><span class="account-label">Account</span><span aria-hidden="true">⌄</span></button>
    {#if profileOpen}<div id="account-menu" class="account-menu"><p>Account services are not connected.</p><button type="button" onclick={() => { profileOpen = false; onworkspace?.(); }}>Workspace</button>
      <!-- TODO(API): Connect authenticated user details, project navigation, and sign-out when supported. -->
      <button type="button" disabled>All Projects</button><button type="button" disabled>New Project</button><button type="button" disabled>Sign Out</button>
    </div>{/if}
  </div>
</header>

<style>
  .app-header,.app-header * { box-sizing:border-box; }
  .app-header { height:48px; width:100%; position:sticky; top:0; z-index:50; flex-shrink:0; display:flex; align-items:center; justify-content:space-between; gap:12px; padding:0 24px; background:#fbfbf9; border-bottom:1px solid #e2e6e2; color:var(--text); font:11px/1.4 var(--sans); text-align:left; }
  button { font:inherit; color:inherit; cursor:pointer; } button:focus-visible { outline:2px solid var(--accent); outline-offset:3px; } button:disabled { cursor:default; opacity:1; color:var(--text-muted); }
  .navigation-left { display:flex; align-items:center; gap:10px; min-width:0; }.brand { display:flex; align-items:center; gap:8px; font-weight:700; letter-spacing:.06em; border:0; padding:0; background:transparent; flex-shrink:0; }.brand-mark { width:24px; height:24px; border-radius:6px; background:var(--accent); }.nav-divider { height:16px; width:1px; background:#e5e8e5; flex-shrink:0; }
  .breadcrumbs { display:flex; align-items:center; gap:7px; min-width:0; border:1px solid #e0e4e0; border-radius:7px; padding:2px 8px 2px 2px; background:#f6f7f5; }.workspace-link { display:flex; align-items:center; gap:5px; border:0; background:transparent; color:var(--text); border-radius:5px; padding:4px 10px; font-weight:500; }.chevron { color:#9aa59f; }.current { padding:4px 8px; border-radius:5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.count { background:#e5ebe5; font-size:9px; border-radius:3px; padding:0 5px; }
  .breadcrumbs .breadcrumb-active { background:var(--accent); color:white; }
  .profile-control { position:relative; flex-shrink:0; }.profile-button { display:flex; align-items:center; gap:8px; border:1px solid #e0e4e0; border-radius:999px; padding:4px 10px 4px 6px; background:white; font-weight:600; }.avatar { display:grid; place-items:center; width:20px; height:20px; border-radius:50%; background:var(--accent); color:white; }.account-menu { position:absolute; right:0; top:calc(100% + 8px); width:190px; padding:5px; border:1px solid var(--border); border-radius:9px; background:var(--surface); box-shadow:0 12px 30px #19282226; }.account-menu p { padding:5px 8px; margin:0; font-size:10px; color:var(--text-muted); border-bottom:1px solid var(--border); }.account-menu button { display:block; text-align:left; width:100%; padding:8px; border:0; border-radius:5px; background:transparent; }.account-menu button:not(:disabled):hover { background:var(--surface-muted); }
  @media(max-width:600px) { .app-header { padding:0 12px; gap:8px; }.navigation-left { gap:7px; }.breadcrumbs { gap:5px; }.workspace-link { padding:4px 6px; }.account-label { display:none; } }
  @media(max-width:420px) { .brand > span:last-child,.nav-divider { display:none; }.current { max-width:125px; }.profile-button { padding:4px 6px; gap:4px; } }
</style>
