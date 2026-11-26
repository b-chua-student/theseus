import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/svelte';

vi.mock('../../lib/api/chat.js', () => ({
  startConversation: vi.fn(),
  askConversation: vi.fn(),
  listConversations: vi.fn(),
  getConversation: vi.fn(),
}));
vi.mock('../../lib/api/sources.js', () => ({ listSources: vi.fn() }));

import { startConversation, askConversation, listConversations, getConversation } from '../../lib/api/chat.js';
import { listSources } from '../../lib/api/sources.js';
import ChatPanel from './ChatPanel.svelte';

// Contract under test (specs/assistant/answer_validation, D-006): askConversation resolves
// `{ answer, citations }` and calls `options.onStatus(message)` when the server reports progress.
// The panel shows that message only while the answer is pending, never a draft, and removes it
// when the answer or an error arrives.

const PROGRESS = 'Checking the answer against your sources…';
const DRAFT = 'The pilot started in May [1] and ended on July 12 [1].';
const CORRECTED = 'The pilot started in May [1] and ended in July [2].';
const TIMEOUT = 'I couldn’t verify an answer within 30 seconds. Please try again.';
const PARTIAL = 'Verified: the pilot started in May [1]. The end date could not be checked in time.';
const INTERRUPTED = 'I couldn’t finish checking this answer. Please try again.';

let pending;

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const editor = { getText: () => '', state: { selection: { empty: true } } };

async function sendQuestion() {
  render(ChatPanel, { projectId: 'p1', editor, tick: 0, open: true, onclose: vi.fn(), notice: '' });
  await fireEvent.click(screen.getByRole('button', { name: 'Source Library' }));
  await fireEvent.input(screen.getByLabelText('Message the assistant'), {
    target: { value: 'When did the pilot start and end?' },
  });
  await fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  await waitFor(() => expect(askConversation).toHaveBeenCalled());
  return vi.mocked(askConversation).mock.calls[0][6];
}

beforeEach(() => {
  vi.resetAllMocks();
  pending = deferred();
  vi.mocked(startConversation).mockResolvedValue('c1');
  vi.mocked(listConversations).mockResolvedValue([]);
  vi.mocked(listSources).mockResolvedValue([]);
  vi.mocked(askConversation).mockReturnValue(pending.promise);
});

describe('ChatPanel answer validation', () => {
  it('S-007: shows no progress until the server reports it, then removes it with the answer', async () => {
    const options = await sendQuestion();

    expect(screen.queryByText(PROGRESS)).not.toBeInTheDocument();

    options.onStatus(PROGRESS);

    expect(await screen.findByText(PROGRESS)).toBeInTheDocument();
    expect(screen.queryByText(/July 12/)).not.toBeInTheDocument();

    pending.resolve({ answer: CORRECTED, citations: [{ key: 1, location: 'P1' }, { key: 2, location: 'P2' }] });

    expect(await screen.findByText(/ended in July/)).toBeInTheDocument();
    expect(screen.queryByText(PROGRESS)).not.toBeInTheDocument();
    expect(screen.queryByText(/July 12/)).not.toBeInTheDocument();
  });

  it('S-007: never displays an unchecked draft while validation is pending', async () => {
    const options = await sendQuestion();
    options.onStatus(PROGRESS);
    await screen.findByText(PROGRESS);

    expect(screen.queryByText(DRAFT)).not.toBeInTheDocument();
    expect(screen.queryByText(/ended on July 12/)).not.toBeInTheDocument();
  });

  it.each([
    ['S-008', PARTIAL, /could not be checked in time/],
    ['S-009', TIMEOUT, /couldn’t verify an answer within 30 seconds/],
    ['S-013', TIMEOUT, /couldn’t verify an answer within 30 seconds/],
  ])('%s: shows the deadline response as the answer and clears progress', async (_id, text, pattern) => {
    const options = await sendQuestion();
    options.onStatus(PROGRESS);
    await screen.findByText(PROGRESS);

    pending.resolve({ answer: text, citations: [] });

    expect(await screen.findByText(pattern)).toBeInTheDocument();
    expect(screen.queryByText(PROGRESS)).not.toBeInTheDocument();
  });

  it('S-004/S-014: shows the direct answer and its sources without a progress event', async () => {
    await sendQuestion();

    pending.resolve({
      answer: CORRECTED,
      citations: [
        { key: 1, location: 'P1', title: 'Pilot report', source_id: 's1' },
        { key: 2, location: 'P2', title: 'Pilot report', source_id: 's1' },
      ],
    });

    expect(await screen.findByText(/ended in July/)).toBeInTheDocument();
    const sources = screen.getByLabelText('Sources cited');
    expect(sources).toHaveTextContent('[1] Pilot report, P1');
    expect(sources).toHaveTextContent('[2] Pilot report, P2');
    expect(screen.queryByText(PROGRESS)).not.toBeInTheDocument();
  });

  it('S-015: shows only accepted pilot findings and citations after progress', async () => {
    const options = await sendQuestion();
    options.onStatus(PROGRESS);
    await screen.findByText(PROGRESS);
    expect(screen.queryByLabelText('Sources cited')).not.toBeInTheDocument();

    pending.resolve({ answer: CORRECTED, citations: [
      { key: 1, location: 'P1', title: 'Pilot report', source_id: 's1' },
      { key: 2, location: 'P2', title: 'Pilot report', source_id: 's1' },
    ] });

    expect(await screen.findByText(/ended in July/)).toBeInTheDocument();
    const sources = screen.getByLabelText('Sources cited');
    expect(sources.querySelectorAll('li')).toHaveLength(2);
    expect(sources).toHaveTextContent('[2] Pilot report, P2');
    expect(screen.queryByText(/August|follow-up/i)).not.toBeInTheDocument();
    expect(screen.queryByText(PROGRESS)).not.toBeInTheDocument();
  });

  it('shows no source list when the answer cites nothing', async () => {
    await sendQuestion();

    pending.resolve({ answer: TIMEOUT, citations: [] });

    expect(await screen.findByText(/couldn’t verify an answer/)).toBeInTheDocument();
    expect(screen.queryByLabelText('Sources cited')).not.toBeInTheDocument();
  });
  it('S-004: a reopened conversation lists the sources each answer cited', async () => {
    vi.mocked(listConversations).mockResolvedValue([{ id: 'c9', title: 'Earlier chat' }]);
    vi.mocked(getConversation).mockResolvedValue({
      context_scope: 'source_library',
      source_ids: null,
      exchanges: [
        {
          query: 'When did it start?',
          answer: CORRECTED,
          asked_at: '2026-11-26T00:00:00Z',
          citations: [{ key: 2, location: 'P2', title: 'Pilot report', source_id: 's1' }],
        },
        { query: 'Older question', answer: 'Older answer', asked_at: '2026-11-25T00:00:00Z' },
      ],
    });
    render(ChatPanel, { projectId: 'p1', editor, tick: 0, open: true, onclose: vi.fn(), notice: '' });

    await screen.findByRole('option', { name: 'Earlier chat' });
    await fireEvent.change(screen.getByLabelText('Saved conversations'), { target: { value: 'c9' } });

    expect(await screen.findByText(/ended in July/)).toBeInTheDocument();
    const lists = screen.getAllByLabelText('Sources cited');
    expect(lists).toHaveLength(1);
    expect(lists[0]).toHaveTextContent('[2] Pilot report, P2');
    expect(screen.getByText('Older answer')).toBeInTheDocument();
  });
  it('S-011/S-017: shows one interruption and does not resubmit the question', async () => {
    const options = await sendQuestion();
    options.onStatus(PROGRESS);
    await screen.findByText(PROGRESS);

    pending.reject(Object.assign(new Error(INTERRUPTED), { status: 502 }));

    expect(await screen.findByText(INTERRUPTED)).toBeInTheDocument();
    expect(askConversation).toHaveBeenCalledTimes(1);
    expect(screen.queryByLabelText('Sources cited')).not.toBeInTheDocument();
    expect(screen.queryByText(PROGRESS)).not.toBeInTheDocument();
    expect(screen.queryByText(/July 12/)).not.toBeInTheDocument();
  });
});
