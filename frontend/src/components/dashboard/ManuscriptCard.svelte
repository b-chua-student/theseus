<script>
  /** @type {{ doc: {id: string, title: string}, onselect: (id: string) => void, onrename: (doc: {id: string, title: string}) => void, ondelete: (doc: {id: string, title: string}) => void, icon: Function }} */
  let { doc, onselect, onrename, ondelete, icon } = $props();

  let menuOpen = $state(false);

  function stopPropagation(fn) {
    return (event) => { event.stopPropagation(); fn(); };
  }
</script>

<svelte:window onclick={() => { menuOpen = false; }} />

<div class="manuscript-card surface">
  <button
    type="button"
    class="card-body"
    onclick={() => onselect?.(doc.id)}
    aria-label={`Open manuscript: ${doc.title}`}
  >
    <span class="card-top">
      <span class="document-badge">{@render icon('document', 11)} Manuscript</span>
    </span>
    <span class="document-title">{doc.title}</span>
    <span class="open-label">Open in Editor <span>›</span></span>
  </button>

  <div class="card-menu">
    <button
      type="button"
      class="menu-trigger"
      onclick={stopPropagation(() => menuOpen = !menuOpen)}
      aria-label="Manuscript actions"
      aria-expanded={menuOpen}
    >
      {@render icon('ellipsis', 14)}
    </button>

    {#if menuOpen}
      <div class="dropdown" role="menu">
        <button
          type="button"
          role="menuitem"
          onclick={stopPropagation(() => { menuOpen = false; onrename?.(doc); })}
        >
          {@render icon('edit', 12)} Rename
        </button>
        <button
          type="button"
          role="menuitem"
          class="danger"
          onclick={stopPropagation(() => { menuOpen = false; ondelete?.(doc); })}
        >
          {@render icon('trash', 12)} Delete
        </button>
      </div>
    {/if}
  </div>
</div>

<style>
  .manuscript-card, .manuscript-card * { box-sizing: border-box; }
  button { font: inherit; color: inherit; cursor: pointer; }
  button:disabled { cursor: default; opacity: 1; }
  button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }

  .surface { background: var(--surface); border: 1.5px solid transparent; border-radius: 14px; box-shadow: var(--shadow); }

  .manuscript-card {
    display: flex;
    align-items: stretch;
    position: relative;
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
  }
  .manuscript-card:hover {
    transform: translateY(-2px);
    border-color: var(--accent);
    box-shadow: 0 10px 22px -4px rgb(30 45 38 / 16%);
  }

  .card-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    padding: 20px;
    text-align: left;
    background: none;
    border: 0;
  }
  .card-body:hover { background: none; }

  .card-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; width: 100%; }
  .document-badge { display: inline-flex; align-items: center; gap: 5px; background: var(--accent); color: white; border-radius: 4px; padding: 3px 8px; font: 500 9px var(--mono); }
  .document-title { display: block; font-size: 14.5px; font-weight: 700; color: var(--text-h); overflow-wrap: anywhere; }
  .open-label { display: inline-flex; align-items: center; gap: 5px; font-size: 10px; font-weight: 700; margin-top: 8px; }
  .open-label > span { font-size: 15px; }

  .card-menu { position: relative; display: flex; align-items: flex-start; padding: 12px 12px 12px 0; }
  .menu-trigger { display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border: 0; border-radius: 6px; background: transparent; color: var(--text-muted); }
  .menu-trigger:hover { background: #e6ece7; color: var(--text); }

  .dropdown {
    position: absolute;
    right: 0;
    top: calc(100% - 4px);
    z-index: 40;
    min-width: 140px;
    background: var(--surface);
    border: 1.5px solid var(--accent-border);
    border-radius: 9px;
    box-shadow: 0 8px 24px #19282228;
    padding: 4px;
    display: flex;
    flex-direction: column;
  }
  .dropdown button {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 10px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    font-size: 11px;
    text-align: left;
  }
  .dropdown button:hover { background: #eff3ef; }
  .dropdown button.danger { color: #b94040; }
  .dropdown button.danger:hover { background: #fdf0f0; }

  @media(max-width: 420px) { .card-body { padding: 16px; } }
  @media(prefers-reduced-motion: reduce) { .manuscript-card { transition: none; } .manuscript-card:hover { transform: none; } }
</style>
