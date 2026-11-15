<script>
  let { documents = [], onselect, oncreate } = $props();

  const formatDate = (ts) => new Date(ts * 1000).toLocaleString();
</script>

<button onclick={() => oncreate?.()}>+ New Document</button>

<table>
  <thead>
    <tr>
      <th>Document</th>
      <th>Author</th>
      <th>Last Modified</th>
      <th>Last Commit</th>
    </tr>
  </thead>
  <tbody>
    {#each documents as doc (doc.document_id)}
      <tr onclick={() => onselect?.(doc.document_id)}>
        <td>{doc.document_id}</td>
        <td>{doc.author}</td>
        <td>{formatDate(doc.last_modified)}</td>
        <td><code>{doc.last_commit_id.slice(0, 7)}</code></td>
      </tr>
    {:else}
      <tr><td colspan="4">No documents</td></tr>
    {/each}
  </tbody>
</table>

<style>
  button { margin-bottom: 1rem; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #ddd; }
  tbody tr { cursor: pointer; }
  tbody tr:hover { background: #f5f5f5; }
</style>
