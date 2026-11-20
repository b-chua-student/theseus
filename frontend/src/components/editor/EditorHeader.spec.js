import { beforeEach, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { createRawSnippet } from 'svelte';
import EditorHeader from './EditorHeader.svelte';
import { listDrafts } from '../../lib/api/drafts.js';
vi.mock('../../lib/api/drafts.js', () => ({ listDrafts:vi.fn(), createDraft:vi.fn(), renameDraft:vi.fn(), deleteDraft:vi.fn(), switchDraft:vi.fn() }));
vi.mock('../../lib/api/indexing.js', () => ({getIndexingStatus:vi.fn().mockResolvedValue({status:'indexed',chunk_count:1})}));
beforeEach(() => { vi.clearAllMocks(); });
const props = () => ({id:'m',projectId:'p',title:'Test',icon:createRawSnippet(() => ({render:() => '<span></span>'})),menuItems:Object.fromEntries(['File','Edit','View','Insert','Format','Tools','Help'].map(x => [x,[]]))});
it('enables merging with two drafts and disables it while saving', async () => {
  listDrafts.mockResolvedValue([{name:'main',is_current:true},{name:'feature'}]);
  const p = props();
  const view = render(EditorHeader, {props:p});
  const button = screen.getByRole('button', {name:'Merge'});
  await waitFor(() => expect(button).toBeEnabled());
  await view.rerender({...p,saving:true});
  expect(button).toBeDisabled();
  expect(button).toHaveAttribute('title','A draft operation is in progress');
});
it('disables merging with one draft', async () => {
  listDrafts.mockResolvedValue([{name:'main',is_current:true}]);
  render(EditorHeader, {props:props()});
  const button = screen.getByRole('button', {name:'Merge'});
  await waitFor(() => expect(listDrafts).toHaveBeenCalled());
  expect(button).toBeDisabled();
  expect(button).toHaveAttribute('title','At least two drafts are required');
});
it('disables merging when tracking has not started', async () => {
  listDrafts.mockRejectedValue(new Error('Not found'));
  render(EditorHeader, {props:props()});
  const button = screen.getByRole('button', {name:'Merge'});
  await waitFor(() => expect(button).toHaveAttribute('title','Draft tracking has not started'));
  expect(button).toBeDisabled();
});
