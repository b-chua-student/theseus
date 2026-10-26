<script>
  import ProjectDashboard from './components/project_dashboard.svelte';
  import DocumentEditor from './components/editor.svelte';

  /** @type {{ id: string; projectId: string; ownerId: string; title: string } | null} */
  let openManuscript = $state(null);

  function openEditor(manuscript) {
    openManuscript = manuscript;
  }

  function back() {
    openManuscript = null;
  }
</script>

{#if openManuscript === null}
  <ProjectDashboard onopen={openEditor} />
{:else}
  <DocumentEditor
    id={openManuscript.id}
    projectId={openManuscript.projectId}
    ownerId={openManuscript.ownerId}
    title={openManuscript.title}
    onback={back}
  />
{/if}
