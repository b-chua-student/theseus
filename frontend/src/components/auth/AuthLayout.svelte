<script>
  import { onMount } from 'svelte';
  import AuthLandingContent from './AuthLandingContent.svelte';
  let { title, subtitle, children } = $props();
  let active = $state('authSection');
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
        {#each sections as section}
          <button class="dot" class:active={active === section.id} aria-label={section.label} aria-current={active === section.id ? 'location' : undefined} title={section.label} onclick={() => navigate(section.id)}><span></span></button>
        {/each}
      </nav>
      <button class="signin" type="button" onclick={() => navigate('authSection')}>↪ Sign In</button>
    </div>
  </header>
  <main>
    <section id="authSection" class="auth-section" aria-label={title}>
      <div class="auth-card">
        <div class="card-brand"><span class="mark"></span><h1>Theseus</h1></div>
        <span class="sr-only">{title}. {subtitle}</span>
        {@render children()}
        <p class="demo">Demo access · Account verification is not connected.</p>
      </div>
    </section>
    <AuthLandingContent onnavigate={navigate} />
  </main>
</div>
<style>
.auth-landing { min-height:100dvh; width:100%; color:var(--text); font-family:var(--sans); background:linear-gradient(125deg,#ffffff61,transparent 42%),radial-gradient(circle at 80% 25%,#a7cebf2e,transparent 55%),var(--bg); }
header { position:sticky; top:0; z-index:30; height:48px; display:flex; align-items:center; justify-content:space-between; padding:0 24px; background:#fbfbf9; border-bottom:1px solid #e2e6e2; }.brand { display:flex; align-items:center; gap:10px; border:0; padding:0; background:none; font-size:11px; font-weight:700; letter-spacing:.06em; }.brand::after { content:''; height:16px; border-right:1px solid #ebebeb; margin-left:8px; }.mark { width:24px; height:24px; border-radius:6px; background:var(--accent); display:block; flex-shrink:0; }.controls { display:flex; align-items:center; gap:10px; }nav { display:flex; padding:1px 5px; border:1px solid #e2e5e2; border-radius:30px; background:white; }.dot { border:0; background:none; padding:7px 3px; display:flex; }.dot span { width:8px; height:8px; border-radius:50%; background:#d8dcd8; }.dot.active span,.dot:hover span { background:#2c3a34; }.signin { background:var(--accent); color:white; border:0; border-radius:6px; padding:6px 12px; font-size:11px; font-weight:500; }
.auth-section { padding:128px 16px; display:flex; justify-content:center; scroll-margin-top:48px; }.auth-card { width:100%; max-width:350px; padding:28px; background:var(--surface); border:1px solid #e8ece8; border-radius:14px; box-shadow:0 6px 24px #1e2d260f; }.card-brand { display:flex; align-items:center; gap:10px; margin-bottom:20px; }.card-brand .mark { width:32px; height:32px; border-radius:7px; }h1 { font-size:17px; letter-spacing:-.025em; margin:0; color:var(--text-h); }.sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); }
.auth-card :global(form) { display:grid; gap:14px; }.auth-card :global(label) { display:grid; gap:4px; font-size:10.5px; font-weight:600; color:#37433d; }.auth-card :global(input) { width:100%; box-sizing:border-box; border:1px solid #dce1dc; border-radius:6px; padding:7px 10px; background:var(--paper); color:var(--text); font:12px var(--sans); }.auth-card :global(button[type=submit]) { background:var(--accent); color:white; padding:8px 12px; border:0; border-radius:6px; font-size:11.5px; font-weight:600; margin-top:4px; }.auth-card :global(button:disabled) { opacity:.6; }.auth-card :global(.switch-row) { margin:16px 0 0; padding-top:16px; position:relative; }.auth-card :global(.switch-row)::before { content:''; width:32px; border-top:1px solid #e2e6e2; position:absolute; top:0; left:calc(50% - 16px); }.auth-card :global(.switch) { width:100%; display:flex; justify-content:space-between; background:white; border:1px solid #e2e5e2; border-radius:6px; padding:6px 12px; color:#2b3530; font-size:10.5px; font-weight:600; }.auth-card :global(.switch:hover) { background:#f4f6f4; }.auth-card :global(.error) { color:#a43c32; font-size:11px; margin:0; }.demo { margin:14px 0 0; font-size:9px; line-height:1.5; color:var(--text-muted); }
@media(max-width:639px) { header { padding:0 16px; }.auth-section { padding:96px 16px; }.auth-card { padding:24px; } }
</style>
