<script module>
  let previousMode;
</script>
<script>
  import { onMount } from 'svelte';
  import AuthLandingContent from './AuthLandingContent.svelte';
  let { title, subtitle, mode, onswitch, children } = $props();
  let active = $state('authSection');
  let indicator;
  const sections = [
    { id:'authSection', label:'Sign In / Sign Up' },
    { id:'heroSection', label:'Research Projects' },
    { id:'cardsSection', label:'Platform Features' },
    { id:'footerSection', label:'Footer' }
  ];
  function navigate(id) {
    document.getElementById(id)?.scrollIntoView({ behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block:'start' });
  }
  onMount(() => {
    if (previousMode && previousMode !== mode && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      indicator?.animate?.([{ transform: previousMode === 'signup' ? 'translateX(100%)' : 'none' }, { transform: mode === 'signup' ? 'translateX(100%)' : 'none' }], { duration: 220, easing: 'ease-out' });
    }
    previousMode = mode;
    function update() {
      const marker = Math.min(window.innerHeight * .35, 240);
      let current = sections[0].id;
      for (const section of sections) {
        if (document.getElementById(section.id)?.getBoundingClientRect().top <= marker) current = section.id;
      }
      if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) current = 'footerSection';
      active = current;
    }
    window.addEventListener('scroll', update, { passive:true });
    window.addEventListener('resize', update);
    update();
    return () => { window.removeEventListener('scroll', update); window.removeEventListener('resize', update); };
  });
</script>
<div class="auth-landing">
  <header>
    <button class="brand" type="button" onclick={() => navigate('authSection')} aria-label="Theseus home"><span class="mark"></span>THESEUS</button>
    <div class="controls">
      <nav aria-label="Landing page sections">
        {#each sections as section (section.id)}
          <button class="dot" class:active={active === section.id} aria-label={section.label} aria-current={active === section.id ? 'location' : undefined} title={section.label} onclick={() => navigate(section.id)}><span></span></button>
        {/each}
      </nav>
      <button aria-label="Sign In" class="signin" type="button" onclick={() => navigate('authSection')}>↪ Sign In</button>
    </div>
  </header>
  <main>
    <section id="authSection" class="auth-section" aria-label={title}>
      <div class="auth-card">
        <div class="brand-panel">
          <div class="card-brand"><span class="mark"></span><h1>Theseus</h1></div>
          <svg class="linework" viewBox="0 0 450 560" preserveAspectRatio="none" aria-hidden="true">
            <path d="M307 0v281l-79 79v76 M386 0v124l-158 157h222 M450 91q-35 33-64 33 M450 202H228l-78 79H0 M150 281l78 79 M150 281v155H0 M0 359h150"/>
          </svg>
          <p>{mode === 'signin' ? 'Welcome back to Theseus.' : 'Create your Theseus account.'}</p>
        </div>
        <div class="form-panel">
          <div class="auth-switch" class:signup={mode === 'signup'} role="group" aria-label="Account access">
            <span class="switch-indicator" aria-hidden="true" bind:this={indicator}></span>
            {#each [['signin', 'Sign In'], ['signup', 'Sign Up']] as [value, label] (value)}
              <button type="button" aria-pressed={mode === value} onclick={() => { if (mode !== value) onswitch?.(); }}>{label}</button>
            {/each}
          </div>
          <span class="sr-only">{title}. {subtitle}</span>
          {@render children()}
        </div>
      </div>
    </section>
    <AuthLandingContent onnavigate={navigate} />
  </main>
</div>
<style>
.auth-landing { min-height:100dvh; width:100%; color:var(--text); font-family:var(--sans); background:linear-gradient(125deg,#ffffff61,transparent 42%),radial-gradient(circle at 80% 25%,#a7cebf2e,transparent 55%),var(--bg); }
header { position:sticky; top:0; z-index:30; height:48px; display:flex; align-items:center; justify-content:space-between; padding:0 24px; background:#fbfbf9; border-bottom:1px solid #e2e6e2; }.brand { display:flex; align-items:center; gap:10px; border:0; padding:0; background:none; font-size:11px; font-weight:700; letter-spacing:.06em; }.brand::after { content:''; height:16px; border-right:1px solid #ebebeb; margin-left:8px; }.mark { width:24px; height:24px; border-radius:6px; background:var(--accent); display:block; flex-shrink:0; }.controls { display:flex; align-items:center; gap:10px; }nav { display:flex; padding:1px 5px; border:1px solid #e2e5e2; border-radius:30px; background:white; }.dot { border:0; background:none; padding:7px 3px; display:flex; }.dot span { width:8px; height:8px; border-radius:50%; background:#d8dcd8; }.dot.active span,.dot:hover span { background:#2c3a34; }.signin { background:var(--accent); color:white; border:0; border-radius:6px; padding:6px 12px; font-size:11px; font-weight:500; }
.auth-section { position:relative; isolation:isolate; overflow:hidden; display:grid; place-items:center; box-sizing:border-box; min-height:calc(100svh - 48px); padding:48px 20px; scroll-margin-top:48px; background:#eaf1eb; }
.auth-section::before {
  content:""; position:absolute; inset:-18%; z-index:-1; pointer-events:none;
  background:radial-gradient(ellipse at 18% 32%, #a9d8c3 0%, transparent 48%),
    radial-gradient(ellipse at 76% 22%, #c1dada 0%, transparent 42%),
    radial-gradient(ellipse at 65% 85%, #ffffff 0%, transparent 45%);
  animation:auth-wave 12s ease-in-out infinite alternate;
}
@keyframes auth-wave {
  from { transform:translate(-4%, -2%) rotate(-4deg); }
  to { transform:translate(5%, 3%) rotate(5deg); }
}
.auth-card { width:min(900px,100%); display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); min-height:560px; overflow:hidden; border-radius:16px; background:white; box-shadow:0 14px 36px #263e3024; }
.brand-panel, .form-panel { padding:clamp(24px,3.3vw,44px); }
.brand-panel { position:relative; isolation:isolate; display:flex; flex-direction:column; justify-content:space-between; background:#d5e1d6; color:#182e24; }
.linework { position:absolute; inset:0; width:100%; height:100%; z-index:-1; fill:none; stroke:#b4c6b7; }
.card-brand { display:flex; align-items:center; gap:12px; }
.card-brand .mark { width:50px; height:50px; border-radius:11px; background:#304f42; }
h1 { margin:0; font-size:30px; letter-spacing:-.03em; color:inherit; }
.brand-panel p { margin:0; font-size:21px; }
.auth-switch { position:relative; isolation:isolate; display:flex; border-radius:30px; padding:4px; margin-bottom:24px; background:#e6e9e8; }
.auth-switch button { flex:1; min-height:44px; border:0; border-radius:24px; background:transparent; color:#47524d; font:600 16px var(--sans); cursor:pointer; }
.switch-indicator {
  content:""; position:absolute; z-index:-1; inset:4px auto 4px 4px; width:calc(50% - 4px);
  border-radius:24px; background:white; box-shadow:0 2px 5px #0003; transition:transform 220ms ease;
}
.auth-switch.signup .switch-indicator { transform:translateX(100%); }
.auth-switch button[aria-pressed=true] { color:#20372c; }

.sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); }
.form-panel :global(form) { display:grid; gap:17px; }
.form-panel :global(label) { display:grid; gap:6px; color:#202b25; font-size:14px; }
.form-panel :global(input) { box-sizing:border-box; width:100%; min-height:40px; padding:8px 12px; border:1px solid #c8cec9; border-radius:8px; background:white; color:#202b25; font:inherit; }
.form-panel :global(button[type=submit]) { min-height:45px; margin-top:4px; border:0; border-radius:8px; background:#304f42; color:white; font:600 16px var(--sans); cursor:pointer; }
.form-panel :global(button:disabled) { opacity:.6; cursor:default; }
.form-panel :global(.error) { margin:0; color:#a43c32; font-size:13px; }
.auth-landing :global(button) {
  transition:background-color 180ms ease, color 180ms ease, border-color 180ms ease, box-shadow 180ms ease, transform 140ms ease;
}
.auth-landing :global(button:active:not(:disabled)) { transform:scale(.98); }
.dot span { transition:background-color 180ms ease; }
@media (hover:hover) {
  .form-panel :global(button[type=submit]:hover:not(:disabled)), .signin:hover { background:#243f34; }
  .auth-switch button:hover { color:#10291d; }
}
@media (prefers-reduced-motion:reduce) {
  .auth-section::before { animation:none; }
  .auth-landing :global(button), .switch-indicator, .dot span { transition:none; }
  .auth-landing :global(button:active:not(:disabled)) { transform:none; }
}
@media(max-width:639px) {
  header { padding:0 16px; }
  .auth-section { padding:28px 16px; }
  .auth-card { max-width:420px; grid-template-columns:1fr; min-height:0; }
  .brand-panel { gap:20px; }
  .card-brand .mark { width:36px; height:36px; }
  h1 { font-size:24px; }
  .brand-panel p { font-size:16px; }
}
</style>
