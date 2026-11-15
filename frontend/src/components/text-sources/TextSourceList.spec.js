import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/svelte';

vi.mock('../../lib/api/textSources.js', () => ({
  listTextSources: vi.fn(),
  searchTextSources: vi.fn(),
  deleteTextSource: vi.fn(),
}));

import { listTextSources, searchTextSources, deleteTextSource } from '../../lib/api/textSources.js';
import TextSourceList from './TextSourceList.svelte';
import TextSourceCard from './TextSourceCard.svelte';

const item = (n, over = {}) => ({
  id: `id${n}`,
  kind: 'text',
  title: `Source ${n}`,
  description: null,
  tags: ['alpha'],
  contentType: 'notes',
  snippet: `snippet ${n}`,
  version: 2,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-02T00:00:00Z',
  ...over,
});
const page = (items, total = items.length) => ({ items, total, page: 1, pageSize: 20 });

const setup = (props = {}) =>
  render(TextSourceList, { projectId: 'p1', onedit: vi.fn(), debounceMs: 0, ...props });

beforeEach(() => {
  vi.resetAllMocks();
  listTextSources.mockResolvedValue(page([item(1), item(2)]));
  searchTextSources.mockResolvedValue(page([item(3)]));
  deleteTextSource.mockResolvedValue(undefined);
});

describe('TextSourceList', () => {
  it('renders cards with title, type, tags and snippet (as text)', async () => {
    listTextSources.mockResolvedValue(
      page([item(1, { title: '<img src=x onerror=alert(1)>', snippet: '<b>hi</b>' })]),
    );
    const { container } = setup();
    expect(await screen.findByText('<img src=x onerror=alert(1)>')).toBeInTheDocument();
    expect(screen.getByText('<b>hi</b>')).toBeInTheDocument();
    expect(container.querySelector('img, b')).toBeNull();
    const card = screen.getByRole('article');
    expect(within(card).getByText('Notes')).toBeInTheDocument();
    expect(screen.getByText('alpha')).toBeInTheDocument();
  });

  it('shows the empty state with a create action when there are no sources', async () => {
    listTextSources.mockResolvedValue(page([]));
    const oncreate = vi.fn();
    setup({ oncreate });
    expect(await screen.findByText('No text sources yet')).toBeInTheDocument();
    await fireEvent.click(screen.getAllByRole('button', { name: '+ Add text' })[1]);
    expect(oncreate).toHaveBeenCalled();
  });

  it('shows a no-results state when filters match nothing', async () => {
    searchTextSources.mockResolvedValue(page([]));
    setup();
    await screen.findByText('Source 1');
    await fireEvent.input(screen.getByPlaceholderText('Search text sources'), { target: { value: 'zzz' } });
    expect(await screen.findByText('No matching text sources')).toBeInTheDocument();
  });

  it('searches using q and disables sort while searching', async () => {
    setup();
    await screen.findByText('Source 1');
    await fireEvent.input(screen.getByPlaceholderText('Search text sources'), { target: { value: ' foo ' } });
    expect(await screen.findByText('Source 3')).toBeInTheDocument();
    expect(searchTextSources).toHaveBeenLastCalledWith('p1', expect.objectContaining({ q: 'foo', page: 1 }));
    expect(screen.getByRole('combobox', { name: 'Sort by' })).toBeDisabled();
  });

  it('applies type filter and sort, resetting to page 1', async () => {
    setup();
    await screen.findByText('Source 1');
    await fireEvent.change(screen.getByRole('combobox', { name: 'Filter by type' }), { target: { value: 'code' } });
    await waitFor(() =>
      expect(listTextSources).toHaveBeenLastCalledWith('p1', expect.objectContaining({ contentType: 'code', page: 1 })),
    );
    await fireEvent.change(screen.getByRole('combobox', { name: 'Sort by' }), { target: { value: 'title' } });
    await waitFor(() =>
      expect(listTextSources).toHaveBeenLastCalledWith('p1', expect.objectContaining({ sort: 'title', contentType: 'code' })),
    );
  });

  it('paginates with Next / Previous', async () => {
    listTextSources.mockResolvedValue(page([item(1)], 45));
    setup({ pageSize: 20 });
    expect(await screen.findByText('Page 1 of 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled();
    await fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(await screen.findByText('Page 2 of 3')).toBeInTheDocument();
    expect(listTextSources).toHaveBeenLastCalledWith('p1', expect.objectContaining({ page: 2, pageSize: 20 }));
  });

  it('opens edit for a card', async () => {
    const onedit = vi.fn();
    setup({ onedit });
    await fireEvent.click(await screen.findByRole('button', { name: 'Edit Source 2' }));
    expect(onedit).toHaveBeenCalledWith(expect.objectContaining({ id: 'id2' }));
  });

  it('requires confirmation before deleting, and cancel does not delete', async () => {
    setup();
    await fireEvent.click(await screen.findByRole('button', { name: 'Delete Source 1' }));
    const dialog = screen.getByRole('alertdialog');
    expect(deleteTextSource).not.toHaveBeenCalled();
    await fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(deleteTextSource).not.toHaveBeenCalled();
  });

  it('deletes after confirm, reloads and notifies', async () => {
    const onchange = vi.fn();
    setup({ onchange });
    await fireEvent.click(await screen.findByRole('button', { name: 'Delete Source 1' }));
    listTextSources.mockResolvedValue(page([item(2)]));
    await fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(screen.queryByText('Source 1')).toBeNull());
    expect(deleteTextSource).toHaveBeenCalledWith('p1', 'id1');
    expect(onchange).toHaveBeenCalled();
  });

  it('keeps the confirm open and shows the error when delete fails', async () => {
    deleteTextSource.mockRejectedValue(new Error('boom'));
    setup();
    await fireEvent.click(await screen.findByRole('button', { name: 'Delete Source 1' }));
    await fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Delete' }));
    expect(await screen.findByText('boom')).toBeInTheDocument();
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('shows an error with retry when loading fails', async () => {
    listTextSources.mockRejectedValueOnce(new Error('down'));
    setup();
    expect(await screen.findByRole('alert')).toHaveTextContent('down');
    await fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('Source 1')).toBeInTheDocument();
  });
});

describe('TextSourceCard', () => {
  it('calls onedit and ondelete with the source', async () => {
    const onedit = vi.fn();
    const ondelete = vi.fn();
    const source = item(1);
    render(TextSourceCard, { source, onedit, ondelete });
    await fireEvent.click(screen.getByRole('button', { name: 'Edit Source 1' }));
    await fireEvent.click(screen.getByRole('button', { name: 'Delete Source 1' }));
    expect(onedit).toHaveBeenCalledWith(source);
    expect(ondelete).toHaveBeenCalledWith(source);
  });
});
