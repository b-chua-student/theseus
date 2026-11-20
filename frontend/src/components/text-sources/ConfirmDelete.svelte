<script>
  /** @type {{ title: string, busy?: boolean, error?: string, onconfirm: () => void, oncancel: () => void }} */
  let { title, busy = false, error = '', onconfirm, oncancel } = $props();

  /** @type {HTMLButtonElement | undefined} */
  let cancelButton = $state();

  // Safe default: focus lands on Cancel so Enter never deletes by accident.
  $effect(() => { cancelButton?.focus(); });
</script>

<div
  class="confirm"
  role="alertdialog"
  aria-modal="true"
  aria-labelledby="confirm-delete-title"
  aria-describedby="confirm-delete-desc"
  tabindex="-1"
  onkeydown={(e) => { if (e.key === 'Escape') oncancel(); }}
>
  <h3 id="confirm-delete-title">Delete text source?</h3>
  <p id="confirm-delete-desc">
    "<strong>{title}</strong>" will be removed from your library and from assistant answers.
  </p>
  {#if error}<p class="error" role="alert">{error}</p>{/if}
  <div class="actions">
    <button type="button" bind:this={cancelButton} onclick={oncancel} disabled={busy}>Cancel</button>
    <button type="button" class="danger" onclick={onconfirm} disabled={busy}>
      {busy ? 'Deleting…' : 'Delete'}
    </button>
  </div>
</div>

<style>
  .confirm { border: 1px solid #e8b4b4; background: #fdf0f0; border-radius: 9px; padding: 14px; margin: 0 0 12px; }
  h3 { margin: 0 0 6px; font-size: 12px; }
  p { margin: 0 0 8px; font-size: 10.5px; overflow-wrap: anywhere; }
  .error { color: #b94040; }
  .actions { display: flex; justify-content: flex-end; gap: 8px; }
  button { font: inherit; font-size: 11px; border: 1px solid #aeb9b3; border-radius: 6px; padding: 6px 12px; background: white; cursor: pointer; }
  button.danger { background: #b94040; border-color: #b94040; color: white; }
  button:disabled { opacity: 0.65; cursor: default; }
  @media (max-width: 767px) { button { min-height: 44px; } .actions { flex-wrap: wrap; } }
  button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
