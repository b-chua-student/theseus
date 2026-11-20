import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/svelte';
import TextSourceForm from './TextSourceForm.svelte';

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
  };
});

const api = await import('../../lib/api/textSources.js');
const KEY = 'theseus:text-draft:p1';

/** @type {import('../../lib/api/textSources.js').TextSource} */
const source = {
  id: 's9',
  kind: 'text',
  title: 'Old',
  content: 'old body',
  description: 'd',
  tags: ['x'],
  contentType: 'notes',
  version: 1,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

const type = (el, value) => fireEvent.input(el, { target: { value } });

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe('TextSourceForm', () => {
  it('shows a live character counter', async () => {
    render(TextSourceForm, { projectId: 'p1' });
    expect(screen.getByText('0 / 100,000')).toBeTruthy();
    await type(screen.getByLabelText('Content'), 'héllo 😀');
    expect(screen.getByText('7 / 100,000')).toBeTruthy(); // code points, not UTF-16 units
  });

  it('flags content over the limit and blocks submit', async () => {
    render(TextSourceForm, { projectId: 'p1' });
    await type(screen.getByLabelText('Title'), 'T');
    await type(screen.getByLabelText('Content'), 'a'.repeat(100001));
    await fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(screen.getByText(/at most 100,000 characters/)).toBeTruthy();
    expect(api.createTextSource).not.toHaveBeenCalled();
  });

  it('previews content as literal text in a <pre>', async () => {
    const { container } = render(TextSourceForm, { projectId: 'p1' });
    const html = '<img src=x onerror=alert(1)><b>hi</b>';
    await type(screen.getByLabelText('Content'), html);
    await fireEvent.click(screen.getByRole('button', { name: 'Preview' }));
    const pre = container.querySelector('pre');
    expect(pre.textContent).toBe(html);
    expect(pre.querySelector('img, b')).toBeNull();
  });

  it('validates required fields and tag count client-side', async () => {
    render(TextSourceForm, { projectId: 'p1' });
    await type(screen.getByLabelText(/Tags/), 'a,b,c,d,e,f,g,h,i,j,k');
    await fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(screen.getByText('Title is required.')).toBeTruthy();
    expect(screen.getByText('Content is required.')).toBeTruthy();
    expect(screen.getByText('Use at most 10 tags.')).toBeTruthy();
    expect(api.createTextSource).not.toHaveBeenCalled();
  });

  it('autosaves a debounced draft and restores it on mount', async () => {
    vi.useFakeTimers();
    const first = render(TextSourceForm, { projectId: 'p1' });
    await type(screen.getByLabelText('Title'), 'My draft');
    await type(screen.getByLabelText('Content'), 'body');
    await vi.advanceTimersByTimeAsync(500);
    expect(localStorage.getItem(KEY)).toBeNull();
    await vi.advanceTimersByTimeAsync(600);
    expect(JSON.parse(localStorage.getItem(KEY))).toMatchObject({ title: 'My draft', content: 'body' });
    first.unmount();

    render(TextSourceForm, { projectId: 'p1' });
    expect(screen.getByLabelText('Title')).toHaveValue('My draft');
    expect(screen.getByLabelText('Content')).toHaveValue('body');
    expect(screen.getByText(/Draft restored/)).toBeTruthy();
  });

  it('creates, normalizes input, and clears the draft', async () => {
    localStorage.setItem(KEY, JSON.stringify({ title: ' Hi ', tags: 'a, b, a,, ', content: 'x' }));
    const created = { ...source, id: 's1', title: 'Hi', content: 'x' };
    vi.mocked(api.createTextSource).mockResolvedValue(created);
    const onsaved = vi.fn();
    render(TextSourceForm, { projectId: 'p1', onsaved });
    await fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    await vi.waitFor(() => expect(onsaved).toHaveBeenCalledWith(created));
    expect(api.createTextSource).toHaveBeenCalledWith('p1', {
      title: 'Hi',
      content: 'x',
      description: undefined,
      tags: ['a', 'b'],
      contentType: 'other',
    });
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  it('edit mode prefills and calls update', async () => {
    vi.mocked(api.updateTextSource).mockResolvedValue({ ...source, version: 2 });
    const onsaved = vi.fn();
    render(TextSourceForm, { projectId: 'p1', source, onsaved });
    expect(screen.getByLabelText('Title')).toHaveValue('Old');
    await type(screen.getByLabelText('Title'), 'New');
    await fireEvent.click(screen.getByRole('button', { name: 'Save changes' }));
    await vi.waitFor(() => expect(onsaved).toHaveBeenCalled());
    expect(api.updateTextSource).toHaveBeenCalledWith(
      'p1',
      's9',
      expect.objectContaining({ title: 'New', contentType: 'notes', tags: ['x'] }),
    );
  });

  it('shows server field errors', async () => {
    vi.mocked(api.createTextSource).mockRejectedValue(
      new api.TextSourceValidationError({ title: 'Title already bad' }),
    );
    render(TextSourceForm, { projectId: 'p1' });
    await type(screen.getByLabelText('Title'), 'T');
    await type(screen.getByLabelText('Content'), 'c');
    await fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(await screen.findByText('Title already bad')).toBeTruthy();
  });
});
