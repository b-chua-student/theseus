<script>
  let { manuscripts = [], onselect, oncreate, ondelete } = $props();

  function remove(e, manuscript) {
    e.stopPropagation();
    if (confirm(`Delete "${manuscript.title}"?`)) ondelete?.(manuscript.id);
  }
</script>

<button class="new" onclick={() => oncreate?.()}>+ New Manuscript</button>

<table>
  <thead>
    <tr>
      <th>Title</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    {#each manuscripts as manuscript (manuscript.id)}
      <tr onclick={() => onselect?.(manuscript.id)}>
        <td>{manuscript.title}</td>
        <td class="actions">
          <button onclick={(e) => remove(e, manuscript)}>Delete</button>
        </td>
      </tr>
    {:else}
      <tr><td colspan="2">No manuscripts</td></tr>
    {/each}
  </tbody>
</table>

<style>
  .new { margin-bottom: 1rem; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #ddd; }
  .actions { text-align: right; width: 1%; white-space: nowrap; }
  tbody tr { cursor: pointer; }
  tbody tr:hover { background: #f5f5f5; }
</style>
