<script>
  import Projects from './pages/projects.svelte';
  import SignIn from './pages/signin.svelte';
  import SignUp from './pages/signup.svelte';
  import { getSession, signOut } from './lib/api/auth.js';
  import AppHeader from "./components/shared/AppHeader.svelte";
  import Dashboard from './pages/dashboard.svelte';
  import DocumentEditor from './pages/editor.svelte';

  let user = $state(getSession());
  let authScreen = $state('signin');
  let showProjects = $state(true);

  // selectedManuscript holds { id, projectId } when the editor is open.
  let selectedManuscript = $state(null);
  let selectedProject = $state(null);
  // Number of manuscripts in the open project, reported by the Dashboard.
  let manuscriptCount = $state(0);
  // Incremented each time the user returns from the editor, so the Dashboard
  // can reload the manuscript list without unmounting and remounting.
  let dashboardRefreshKey = $state(0);

  async function handleSignOut() {
    await signOut();
    user = null;
  }

  function openProject(project) {
    selectedProject = project;
    showProjects = false;
  }

  function openManuscript(manuscriptId, projectId, title) {
    selectedManuscript = { id: manuscriptId, projectId, title };
  }

  function backFromEditor() {
    selectedManuscript = null;
    dashboardRefreshKey++;
  }

  function backToProjects() {
    selectedProject = null;
    selectedManuscript = null;
    showProjects = true;
  }
</script>

{#if !user}
  {#if authScreen === 'signup'}
    <SignUp onsuccess={value => user = value} onswitch={() => authScreen = 'signin'} />
  {:else}
    <SignIn onsuccess={value => user = value} onswitch={() => authScreen = 'signup'} />
  {/if}
{:else}
  <AppHeader
    inEditor={selectedManuscript !== null}
    documentTitle={selectedManuscript?.title ?? ''}
    manuscriptCount={showProjects ? 0 : manuscriptCount}
    onworkspace={() => { selectedManuscript = null; showProjects = true; }}
    onsignout={handleSignOut}
  />

  {#if showProjects}
    <Projects {user} onworkspace={() => showProjects = false} onproject={openProject} />
  {:else}
    <!--
      Keep the Dashboard mounted while the editor is open (hidden via CSS) so its
      loading state and manuscript list are preserved. Without this, every trip
      through the editor destroys and recreates the Dashboard, causing it to
      re-run load() on return — which shows "Loading manuscripts…" unnecessarily
      and can get stuck if the back-navigation races with an in-flight save.
    -->
    <div class:hidden={selectedManuscript !== null}>
      <Dashboard
        {selectedProject}
        refreshKey={dashboardRefreshKey}
        oncount={(count) => manuscriptCount = count}
        onselect={openManuscript}
        onback={backToProjects}
      />
    </div>
    {#if selectedManuscript !== null}
      <div class="editor-screen">
        <DocumentEditor
          manuscriptId={selectedManuscript.id}
          projectId={selectedManuscript.projectId}
          title={selectedManuscript.title}
          onback={backFromEditor}
        />
      </div>
    {/if}
  {/if}
{/if}

<style>
  /* Hide the dashboard behind the editor without unmounting it, so its loaded
     manuscript list and loading state are preserved across editor visits. */
  .hidden {
    display: none;
  }

  /* Keep the document workspace below the shared 48px navigation. */
  .editor-screen {
    position: fixed;
    inset: 48px 0 0;
    z-index: 10;
    overflow: auto;
    background: #e3eae5;
    text-align: left;
    color-scheme: light;
  }

  /* Fill the viewport space below AppHeader. */
  .editor-screen > :global(.theseus-editor) {
    width: 100%;
    max-width: none;
    height: calc(100dvh - 48px);
    min-height: 0;
    margin: 0;
  }

  /* Prevent the underlying dashboard container from scrolling behind the editor. */
  :global(body:has(.editor-screen)) {
    overflow: hidden;
  }

  /* Preserve the editor's stacked, scrollable layout on smaller screens. */
  @media (max-width: 1023px) {
    .editor-screen > :global(.theseus-editor) {
      height: auto;
      min-height: calc(100dvh - 48px);
    }
  }
</style>
