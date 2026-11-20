import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { readFileSync } from 'node:fs';

vi.mock('../../lib/api/textSources.js', async () => {
  class TextSourceValidationError extends Error {
    constructor(fieldErrors, message = 'Please fix the highlighted fields.') {
      super(message);
      this.fieldErrors = fieldErrors;
    }
  }
  return {
    TextSourceValidationError,
    createTextSource: vi.fn(),
    updateTextSource: vi.fn(),
    listTextSources: vi.fn(),
    searchTextSources: vi.fn(),
    deleteTextSource: vi.fn(),
  };
});

import { listTextSources, deleteTextSource } from '../../lib/api/textSources.js';
import TextSourceForm from './TextSourceForm.svelte';
import TextSourceList from './TextSourceList.svelte';

/** @returns {import('../../lib/api/textSources.js').TextSourceSummary} */
const item = (n) => ({
  id: `id${n}`,
  kind: 'text',
  title: `Source ${n}`,
  description: null,
  tags: ['alpha'],
  contentType: 'notes',
  snippet: `snippet ${n}`,
  version: 1,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-02T00:00:00Z',
});

// color-contrast and region need real layout/page context that jsdom lacks.
const audit = (node) =>
  axe.run(node, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false } } });

beforeEach(() => {
  localStorage.clear();
  vi.resetAllMocks();
  vi.mocked(listTextSources).mockResolvedValue({ items: [item(1), item(2)], total: 2, page: 1, pageSize: 20 });
  vi.mocked(deleteTextSource).mockResolvedValue(undefined);
});
afterEach(cleanup);

describe('text source accessibility', () => {
  it('form has no axe violations, including in the error state', async () => {
    const { container } = render(TextSourceForm, { projectId: 'p1', oncancel: () => {} });
    expect((await audit(container)).violations).toEqual([]);
    await fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(screen.getByLabelText('Title')).toHaveAttribute('aria-invalid', 'true');
    expect((await audit(container)).violations).toEqual([]);
  });

  it('list (with cards and delete confirm) has no axe violations', async () => {
    const { container } = render(TextSourceList, { projectId: 'p1', onedit: vi.fn(), oncreate: vi.fn(), debounceMs: 0 });
    await screen.findByText('Source 1');
    expect((await audit(container)).violations).toEqual([]);
    await fireEvent.click(screen.getByRole('button', { name: 'Delete Source 1' }));
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect((await audit(container)).violations).toEqual([]);
  });

  it('every form control has an accessible label', () => {
    render(TextSourceForm, { projectId: 'p1' });
    for (const name of ['Title', 'Type', 'Description (optional)', /^Tags/, 'Content']) {
      expect(screen.getByLabelText(name)).toBeInTheDocument();
    }
  });

  it('reaches every field and button with Tab in order', async () => {
    const user = userEvent.setup();
    render(TextSourceForm, { projectId: 'p1', oncancel: () => {} });
    const order = [];
    for (let i = 0; i < 7; i++) {
      await user.tab();
      order.push(document.activeElement.id || document.activeElement.textContent.trim());
    }
    expect(order).toEqual([
      'tsf-title', 'tsf-contentType', 'tsf-description', 'tsf-tags', 'Preview', 'tsf-content', 'Create',
    ]);
    await user.tab();
    expect(document.activeElement).toHaveTextContent('Cancel');
  });

  it('announces errors in a persistent live region and focuses the first invalid field', async () => {
    render(TextSourceForm, { projectId: 'p1' });
    const live = screen.getByRole('status');
    expect(live).toHaveAttribute('aria-live', 'polite');
    await fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    await waitFor(() => expect(live).toHaveTextContent('The form has 2 errors. Check: title, content.'));
    expect(document.activeElement).toBe(screen.getByLabelText('Title'));
    expect(screen.getByLabelText('Title')).toHaveAccessibleDescription('Title is required.');
  });

  it('returns focus to the content field when leaving preview', async () => {
    const user = userEvent.setup();
    render(TextSourceForm, { projectId: 'p1' });
    await user.click(screen.getByRole('button', { name: 'Preview' }));
    await user.click(screen.getByRole('button', { name: 'Edit' }));
    expect(document.activeElement).toBe(screen.getByLabelText('Content'));
  });

  it('delete confirm focuses Cancel, closes on Escape, and restores focus to the trigger', async () => {
    const user = userEvent.setup();
    render(TextSourceList, { projectId: 'p1', onedit: vi.fn(), debounceMs: 0 });
    const trigger = await screen.findByRole('button', { name: 'Delete Source 1' });
    await user.click(trigger);
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Cancel' })));
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
    expect(document.activeElement).toBe(trigger);
  });
});

describe('responsive layout', () => {
  const css = (f) => readFileSync(new URL(f, import.meta.url), 'utf8');

  it('form stacks on mobile and goes two-column from tablet width', () => {
    const s = css('./TextSourceForm.svelte');
    expect(s).toMatch(/grid-template-columns:\s*1fr;/);
    expect(s).toMatch(/@media \(min-width: 768px\)[\s\S]*grid-template-columns:\s*minmax\(0, 1fr\) minmax\(0, 2fr\)/);
  });

  it('prevents horizontal overflow from long content and uses touch-sized targets on mobile', () => {
    expect(css('./TextSourceForm.svelte')).toMatch(/overflow-wrap:\s*anywhere/);
    expect(css('./TextSourceCard.svelte')).toMatch(/overflow-wrap:\s*anywhere/);
    expect(css('./TextSourceList.svelte')).toMatch(/@media \(max-width: 767px\)[\s\S]*min-height: 44px/);
    expect(css('./TextSourceForm.svelte')).toMatch(/min-height:\s*44px/);
  });
});
