import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import ChatPanel from './ChatPanel.svelte';

const FIRST = '11111111-1111-4111-8111-111111111111';
const SECOND = '22222222-2222-4222-8222-222222222222';
const QUOTE = 'Children recovered in 5 days';

/** Every request succeeds with an empty list; these tests only care about local state. */
const fetchStub = vi.fn(async () => ({
  ok: true, status: 200, headers: new Headers(), json: async () => [],
}));

function editorWithSelection() {
  const text = `Adults recovered in 8 days. ${QUOTE}.`;
  const from = text.indexOf(QUOTE);
  return {
    getText: () => text,
    state: {
      selection: { empty: false, from, to: from + QUOTE.length },
      doc: { textBetween: (a, b) => text.slice(a, b) },
    },
  };
}

async function quoteTheSelection(user) {
  await user.click(await screen.findByRole('button', { name: 'Quote selection' }));
  await screen.findByText(QUOTE);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  fetchStub.mockClear();
});

describe('ChatPanel quote when the project changes', () => {
  it('drops a quote taken in the previous project', async () => {
    vi.stubGlobal('fetch', fetchStub);
    const user = userEvent.setup();
    const view = render(ChatPanel, {
      props: { projectId: FIRST, editor: editorWithSelection(), tick: 0, open: true, onclose: vi.fn(), notice: '' },
    });
    await quoteTheSelection(user);

    await view.rerender({ projectId: SECOND });

    await waitFor(() => expect(screen.queryByText(QUOTE)).toBeNull());
    expect(screen.queryByText('QUOTED')).toBeNull();
  });

  it('keeps the quote while the project stays the same', async () => {
    vi.stubGlobal('fetch', fetchStub);
    const user = userEvent.setup();
    const view = render(ChatPanel, {
      props: { projectId: FIRST, editor: editorWithSelection(), tick: 0, open: true, onclose: vi.fn(), notice: '' },
    });
    await quoteTheSelection(user);

    await view.rerender({ projectId: FIRST, tick: 1 });

    expect(screen.getByText(QUOTE)).toBeInTheDocument();
  });
});
