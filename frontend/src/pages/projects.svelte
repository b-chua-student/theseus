<script>
  let { user, onworkspace } = $props();
  let projects = $state([]), modal, name = $state(''), description = $state(''), member = $state(''), members = $state([]);
  function open() { name=''; description=''; member=''; members=[]; modal.showModal(); }
  function add() { const value=member.trim(); if(value && !members.includes(value)) members=[...members,value]; member=''; }
  function create(event) {
    event.preventDefault(); if(!name.trim()) return;
    // TODO(API): persist project and resolve member IDs through lib/api/projects.js.
    // Demo cards exist in memory only. No accounts are searched or invited.
    projects=[...projects,{id:crypto.randomUUID(),name:name.trim(),description:description.trim(),members:[...members]}]; modal.close();
  }
</script>
<section class="banner"><div><span class="eyebrow">THESEUS PROJECTS</span><h1>Welcome {user?.name || 'Researcher'}! Lets Continue Your Research Projects</h1><p>Select a project to view its manuscripts and source library.</p></div></section>
<main><div class="toolbar"><span>YOUR PROJECTS · {projects.length}</span><button onclick={onworkspace}>Open existing manuscript workspace ↗</button></div><div class="grid">
<button class="card new" onclick={open}><span class="plus">+</span><strong>New Project</strong><small>Create a research workspace</small></button>
{#each projects as project (project.id)}
<article class="card"><h2>{project.name}</h2><p>{project.description || 'No description added.'}</p><div class="meta">0 manuscripts · {project.members.length + 1} members</div><small>Local preview · Project workspace coming soon</small></article>
{/each}
</div><p class="note">Demo projects last until you leave or reload this page.</p></main>
<dialog bind:this={modal} aria-labelledby="creation-title">
<header><strong id="creation-title">Project Creation</strong><button onclick={() => modal.close()} aria-label="Close project creation">×</button></header>
<form onsubmit={create}>
<label>Project Name<input bind:value={name} required maxlength="120" placeholder="e.g., Project - 1, name..." /></label>
<label>Project Description (Optional)<input bind:value={description} placeholder="e.g., Project for science..." /></label>
<div class="member-section"><label for="member">SEARCH MEMBER</label><div class="search"><input id="member" bind:value={member} placeholder="Search Account" onkeydown={e => { if(e.key==='Enter'){e.preventDefault();add();} }} /><button type="button" class="green" onclick={add}>Add +</button></div>
<!-- TODO(API): search real accounts and submit invitations when backend support exists. -->
<div class="chips">{#each members as item}<span>{item}<button type="button" aria-label={'Remove '+item} onclick={() => members=members.filter(x=>x!==item)}>×</button></span>{:else}<small>No additional members added yet.</small>{/each}</div><small>Member names are preview labels only.</small></div>
<footer><button class="green" type="submit">Create +</button></footer>
</form></dialog>
<style>
.banner{padding:36px 24px;background:linear-gradient(125deg,#6e857b,#839e93 34%,#9cc1b3 68%,#b2dec8);color:white}.banner>div{max-width:780px;margin:auto}.eyebrow{font:9.5px var(--mono);letter-spacing:.08em}h1{font-size:23px;max-width:540px;line-height:1.35;margin:8px 0}p{font-size:11px;line-height:1.6}main{max-width:844px;margin:auto;padding:48px 32px}.toolbar{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:20px;font:10px var(--mono)}button{cursor:pointer}.toolbar button{background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:8px;font:11px var(--sans)}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.card{background:var(--surface);padding:24px;border:1.5px solid transparent;border-radius:14px;min-height:255px;box-shadow:var(--shadow);overflow-wrap:anywhere}.new{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px}.new:hover{border-color:var(--accent)}.plus{font-size:32px;color:var(--accent)}h2{font-size:14px;margin:0 0 12px}small,.meta,.note{font-size:10px;color:var(--text-muted)}.meta{margin:28px 0 12px}.note{margin-top:20px}dialog{padding:0;width:calc(100% - 32px);max-width:365px;max-height:90dvh;overflow:auto;border:1.5px solid #526b60;border-radius:12px;background:var(--surface);color:var(--text);box-shadow:0 18px 45px #19282238}dialog::backdrop{background:#17251e66;backdrop-filter:blur(3px)}header{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid var(--border);font-size:11px}header button,.chips button{border:0;background:none;font-size:18px}form{padding:20px;display:grid;gap:16px}label{display:grid;gap:8px;font-size:13px;font-weight:700}input{width:100%;min-width:0;padding:7px 12px;background:white;border:1px solid var(--border);border-radius:6px;font-size:11px}form>label{padding-bottom:16px;border-bottom:1px solid var(--border)}.member-section>label{font:9px var(--mono);color:var(--text-muted)}.search{display:flex;gap:10px;margin:8px 0 12px}.green{background:var(--accent);color:white;border:0;border-radius:5px;padding:7px 16px;font-size:10.5px;white-space:nowrap}.chips{min-height:96px;padding:10px;background:white;border:1px solid var(--border);border-radius:8px;display:flex;align-content:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:8px}.chips>span{display:flex;align-items:center;gap:6px;border:1px solid #7c8b84;border-radius:6px;padding:3px 8px;font-size:10px}footer{text-align:right}@media(max-width:760px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:500px){.grid{grid-template-columns:1fr}main{padding:28px 16px}.toolbar{flex-direction:column;align-items:flex-start}}
</style>
