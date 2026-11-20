<script>
  import { onMount } from 'svelte';
  import { mergeDraft } from '../../lib/api/drafts.js';
  import { conflictKey, carryOverChoices, toResolutions, valuePreview } from '../../lib/mergeDraft.js';
  let { projectId, id, currentDraft, drafts, hasUnsavedChanges = false, onmerged, onclose } = $props();
  let dialog;
  let source = $state('');
  let conflicts = $state([]);
  let choices = $state({});
  let busy = $state(false);
  let error = $state('');
  let disabled = $derived(!source || hasUnsavedChanges || busy || conflicts.some(c => !choices[conflictKey(c)]));
  onMount(() => { dialog.showModal(); });
  async function submit(event) {
    event.preventDefault();
    if (disabled) return;
    busy = true;
    error = '';
    try {
      await mergeDraft(projectId, id, source, { resolutions: toResolutions(conflicts, choices) });
      await onmerged(source, currentDraft);
    } catch (e) {
      if (e.code === 'revision.merge_conflict') {
        conflicts = e.conflicts ?? [];
        choices = carryOverChoices(choices, conflicts);
      } else {
        error = e.code === 'revision.no_changes' ? 'Nothing new to merge.' : `Merge failed: ${e.message}`;
      }
    } finally { busy = false; }
  }
</script>

<dialog bind:this={dialog} aria-modal="true" aria-labelledby="merge-title" oncancel={() => onclose()}>
  <form onsubmit={submit}>
    <h2 id="merge-title">Merge drafts</h2>
    <p>Target draft: <strong>{currentDraft}</strong></p>
    <label>Source draft
      <select bind:value={source} disabled={busy} onchange={() => { conflicts = []; choices = {}; error = ''; }}>
        <option value="">Choose a draft</option>
        {#each drafts.filter(d => d.name !== currentDraft) as draft (draft.name)}
          <option value={draft.name}>{draft.name}</option>
        {/each}
      </select>
    </label>
    {#if hasUnsavedChanges}<p role="status">Save your changes before merging.</p>{/if}
    {#each conflicts as conflict (`${conflict.section_id}:${conflict.field}`)}
      <fieldset>
        <legend>{conflict.section_heading}, {conflict.field}</legend>
        {#each ['target', 'source'] as side (side)}
          <label class="choice">
            <input type="radio" name={`${conflict.section_id}:${conflict.field}`} value={side}
              checked={choices[conflictKey(conflict)] === side} disabled={busy}
              onchange={() => choices = { ...choices, [conflictKey(conflict)]: side }}
              aria-label={`${conflict.section_heading} ${conflict.field}: ${side}`} />
            <span><strong>{side === 'target' ? 'Target' : 'Source'}</strong>: {valuePreview(conflict.field, conflict[side])}</span>
          </label>
        {/each}
      </fieldset>
    {/each}
    {#if error}<p role="alert">{error}</p>{/if}
    {#if busy}<p role="status">Merging…</p>{/if}
    <footer><button type="button" onclick={onclose}>Cancel</button><button type="submit" {disabled}>Merge</button></footer>
  </form>
</dialog>

<style>
  dialog { width: min(600px, calc(100vw - 48px)); max-height: 80vh; overflow: auto; border: 1px solid #aeb9b3; border-radius: 12px; padding: 24px; background: var(--surface, white); color: var(--text, #203528); }
  dialog::backdrop { background: #19282266; }
  label { display: grid; gap: 8px; }
  select, button { font: inherit; padding: 8px 12px; }
  fieldset { margin: 16px 0; border: 1px solid #aeb9b3; }
  .choice { display: flex; align-items: start; padding: 8px; overflow-wrap: anywhere; }
  footer { display: flex; justify-content: end; gap: 8px; margin-top: 20px; }
  button:disabled { opacity: .5; }
</style>
