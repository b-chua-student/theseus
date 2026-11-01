<script>
  let { onnavigate } = $props();
  const features = [{"title": "About Theseus", "body": "Theseus is a modern academic workspace built for researchers, thesis writers, and lab teams. Write structured manuscripts, manage section revisions, and keep every claim grounded in your verified literature.", "badge": "TH \u00b7 DOCS"}, {"title": "Create Projects", "body": "Set up dedicated research repositories for your thesis, journal submissions, or lab studies. Organize multiple manuscript drafts, track branch diffs, and manage citations in APA or IEEE format.", "badge": "EV \u00b7 MT \u00b7 SK"}, {"title": "AI Assistant", "body": "Ask questions directly against your manuscript sections and uploaded PDF sources. Every response is grounded in your indexed project chunks with clear page references and zero cross-project noise.", "badge": "EV \u00b7 NK"}, {"title": "Discover Research Papers", "body": "Upload and index PDF literature into your project source library. Automatically extract metadata, verify DOIs, and keep key findings ready to cite while you write your manuscript.", "badge": "EV \u00b7 AL"}, {"title": "Collab", "body": "Invite co-authors, editors, and faculty supervisors to your project. Work on different sections simultaneously, review branch changes, and merge revisions without overwriting each other's work.", "badge": "EV \u00b7 NK"}];
</script>
<section id="heroSection" class="banner hero">
  <div class="hero-inner">
    <div class="intro"><span class="eyebrow">THESEUS PROJECTS</span>
      <h2>Make your Research Projects</h2>
      <p>Draft, branch, and organize academic manuscripts in one unified workspace. Structure sections with version control, connect your PDF source library for grounded citations, and collaborate seamlessly with co-authors and advisors from first outline to final publication.</p>
    </div>
    <svg class="illustration" aria-hidden="true" viewBox="0 0 280 220" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="38" y="34" width="184" height="128" rx="8" fill="#7C988D" stroke="#1E2824" stroke-width="2.5"/>
                <line x1="38" y1="52" x2="222" y2="52" stroke="#1E2824" stroke-width="2.2"/>
                <circle cx="50" cy="43" r="3" fill="#F4F6F4" stroke="#1E2824" stroke-width="1.5"/>
                <circle cx="60" cy="43" r="3" fill="#9EBDB0" stroke="#1E2824" stroke-width="1.5"/>
                <circle cx="70" cy="43" r="3" fill="#6D877D" stroke="#1E2824" stroke-width="1.5"/>
                <rect x="48" y="62" width="42" height="88" rx="4" fill="#9EBDB0" stroke="#1E2824" stroke-width="2"/>
                <line x1="55" y1="74" x2="82" y2="74" stroke="#1E2824" stroke-width="2.5" stroke-linecap="round"/>
                <line x1="55" y1="84" x2="78" y2="84" stroke="#1E2824" stroke-width="2" stroke-linecap="round"/>
                <line x1="55" y1="94" x2="80" y2="94" stroke="#1E2824" stroke-width="2" stroke-linecap="round"/>
                <line x1="55" y1="104" x2="74" y2="104" stroke="#1E2824" stroke-width="2" stroke-linecap="round"/>
                <g transform="rotate(3 156 112)">
                  <rect x="102" y="54" width="106" height="126" rx="5" fill="#FFFFFF" stroke="#1E2824" stroke-width="2.5"/>
                  <rect x="112" y="68" width="86" height="44" rx="4" fill="#E8F3EE" stroke="#3B5B4F" stroke-width="2"/>
                  <line x1="120" y1="79" x2="154" y2="79" stroke="#1E2824" stroke-width="3" stroke-linecap="round"/>
                  <line x1="120" y1="90" x2="188" y2="90" stroke="#1E2824" stroke-width="2.2" stroke-linecap="round"/>
                  <line x1="120" y1="99" x2="178" y2="99" stroke="#1E2824" stroke-width="2.2" stroke-linecap="round"/>
                  <line x1="114" y1="126" x2="148" y2="126" stroke="#1E2824" stroke-width="3" stroke-linecap="round"/>
                  <line x1="114" y1="138" x2="192" y2="138" stroke="#1E2824" stroke-width="2.2" stroke-linecap="round"/>
                  <line x1="114" y1="148" x2="184" y2="148" stroke="#1E2824" stroke-width="2.2" stroke-linecap="round"/>
                  <line x1="114" y1="158" x2="166" y2="158" stroke="#1E2824" stroke-width="2.2" stroke-linecap="round"/>
                </g>
                <rect x="28" y="132" width="76" height="46" rx="8" fill="#F4F6F4" stroke="#1E2824" stroke-width="2.5"/>
                <path d="M44 164V146C44 146 54 146 58 154C62 162 72 162 72 162" stroke="#1E2824" stroke-width="2.2" stroke-linecap="round"/>
                <circle cx="44" cy="164" r="4.5" fill="#3B5B4F" stroke="#1E2824" stroke-width="2"/>
                <circle cx="44" cy="146" r="4.5" fill="#9EBDB0" stroke="#1E2824" stroke-width="2"/>
                <circle cx="74" cy="162" r="4.5" fill="#B5D8C8" stroke="#1E2824" stroke-width="2"/>
                <circle cx="86" cy="146" r="4.5" fill="#3B5B4F" stroke="#1E2824" stroke-width="2"/>
                <line x1="48.5" y1="146" x2="81.5" y2="146" stroke="#1E2824" stroke-width="2.2"/>
                <circle cx="222" cy="148" r="26" fill="#B5D8C8" stroke="#1E2824" stroke-width="2.5"/>
                <circle cx="222" cy="148" r="19" fill="#F4F6F4" stroke="#1E2824" stroke-width="2"/>
                <path d="M222 135L225 144L234 147L225 150L222 159L219 150L210 147L219 144L222 135Z" fill="#7C988D" stroke="#1E2824" stroke-width="1.8" stroke-linejoin="round"/>
                <path d="M240 60L243 68L251 71L243 74L240 82L237 74L229 71L237 68L240 60Z" fill="#E8F3EE" stroke="#1E2824" stroke-width="1.8" stroke-linejoin="round"/>
                <path d="M24 78V88M19 83H29" stroke="#1E2824" stroke-width="2" stroke-linecap="round"/>
                <path d="M254 96L255.5 101L260.5 102.5L255.5 104L254 109L252.5 104L247.5 102.5L252.5 101L254 96Z" fill="#E8F3EE" stroke="#1E2824" stroke-width="1.5" stroke-linejoin="round"/>
              </svg>
  </div>
</section>
<section id="cardsSection" class="features" aria-label="Platform features">
  <div class="grid">
    {#each features as feature}
      <!-- UI only: direct visitors to the form until project navigation is connected. -->
      <button type="button" class="feature" onclick={() => onnavigate('authSection')}>
        <div><h3>{feature.title}</h3><p>{feature.body}</p></div>
        <span class="badge">{feature.badge}</span>
      </button>
    {/each}
  </div>
</section>
<footer id="footerSection">
  <div class="banner footer-banner"><div class="footer-inner">
    <div class="footer-grid">
      <div><span class="eyebrow">THESEUS PROJECTS</span><h2>THESEUS</h2><p>A collaborative research and manuscript authoring platform for academic teams. Manage branched drafts, section-level version history, indexed PDF source libraries, and grounded AI synthesis in one place.</p></div>
      <nav aria-label="Platform"><span class="eyebrow">Platform</span>
        {#each ['Sign In / Register', 'Projects Directory', 'Manuscript Editor', 'Source Library & AI'] as label}
          <button type="button" onclick={() => onnavigate('authSection')}>{label}</button>
        {/each}
      </nav>
      <nav aria-label="Resources"><span class="eyebrow">Resources</span>
        <button type="button" onclick={() => onnavigate('heroSection')}>About Us</button>
        <button type="button" onclick={() => onnavigate('cardsSection')}>Documentation &amp; Guides</button>
        <!-- TODO: connect real policy content when available. -->
        <button type="button" disabled title="Coming soon">Privacy &amp; Terms</button>
        <span class="contact">support@theseus.com</span>
      </nav>
    </div>
    <div class="copyright"><span>© {new Date().getFullYear()} Theseus Research Platform. All rights reserved.</span><span class="version">Version 1.0 · Interactive Prototype</span></div>
  </div></div>
</footer>
<style>
section,footer { scroll-margin-top:64px; }
.banner { background:linear-gradient(125deg,#6e857b 0%,#839e93 34%,#9cc1b3 68%,#b2dec8 100%); color:white; position:relative; }
.banner::before { content:''; position:absolute; inset:0; background:linear-gradient(115deg,#ffffff05 0%,#ffffff1f 48%,#ffffff00 52%); pointer-events:none; }
.hero { padding:128px clamp(24px,8vw,128px); }.hero-inner,.footer-inner { max-width:896px; margin:auto; position:relative; }.hero-inner { display:flex; align-items:center; justify-content:space-between; gap:40px; }.intro { max-width:448px; }.eyebrow { font:10px var(--mono); letter-spacing:.08em; text-transform:uppercase; opacity:.8; }h2 { font-size:26px; line-height:1.35; letter-spacing:-.025em; margin:6px 0 10px; }p { font-size:11.5px; line-height:1.65; margin:0; opacity:.9; }.illustration { width:240px; height:auto; flex-shrink:0; }.features { padding:112px 32px; }.grid { max-width:780px; margin:auto; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:20px; }.feature { text-align:left; background:var(--surface); border:1.5px solid transparent; border-radius:14px; padding:24px; min-height:260px; display:flex; flex-direction:column; justify-content:space-between; gap:16px; box-shadow:var(--shadow); transition:transform .18s,border-color .18s; }.feature:hover { transform:translateY(-2px); border-color:var(--accent); }h3 { font-size:14px; margin:0 0 8px; color:var(--text-h); }.feature p { font-size:10.5px; line-height:1.55; color:var(--text-muted); opacity:1; }.badge { width:fit-content; background:#e4e7e4; color:var(--accent); border-radius:20px; font-size:8.5px; font-weight:700; padding:4px 8px; }footer { padding-bottom:40px; }.footer-banner { padding:96px clamp(24px,8vw,128px); }.footer-grid { display:grid; grid-template-columns:2fr 1fr 1fr; gap:32px; padding-bottom:40px; border-bottom:1px solid #ffffff33; }.footer-grid h2 { font-size:22px; }.footer-grid p { font-size:11px; }nav { display:flex; flex-direction:column; align-items:flex-start; gap:6px; }nav .eyebrow { margin-bottom:2px; }nav button { padding:0; border:0; background:none; color:inherit; font-size:11px; text-align:left; }nav button:disabled { opacity:.55; }.contact { font-size:10px; opacity:.8; margin-top:4px; }.copyright { display:flex; justify-content:space-between; gap:8px; padding-top:20px; font-size:10px; opacity:.8; }.version { font:9.5px var(--mono); }
@media(max-width:1023px) { .grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media(max-width:767px) { .hero-inner { flex-direction:column; }.footer-grid { grid-template-columns:1fr; }.copyright { flex-direction:column; align-items:center; text-align:center; } }
@media(max-width:639px) { .hero { padding:96px 24px; }.features { padding:80px 16px; }.grid { grid-template-columns:1fr; }.illustration { width:208px; }.footer-banner { padding:80px 24px; }h2 { font-size:24px; } }
@media(prefers-reduced-motion:reduce) { .feature { transition:none; } }
</style>
