import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { askConversation } from './chat.js';

// Contract under test (specs/assistant/answer_validation, D-006):
//  - askConversation resolves `{ answer, citations }`.
//  - It asks for newline-delimited JSON (`Accept: application/x-ndjson`) and also accepts the
//    plain JSON body the endpoint returns today.
//  - Stream records are `{type:'status', message}`, `{type:'answer', answer, citations}` and
//    `{type:'error', error}`. `options.onStatus(message)` is called for each status record.

const PROGRESS = 'Checking the answer against your sources…';
const CITATIONS = [
  { key: 1, location: 'P1' },
  { key: 2, location: 'P2' },
];
const CORRECTED = 'The pilot started in May [1] and ended in July [2].';

const fetchMock = vi.fn();
const encoder = new TextEncoder();

function streamOf(...chunks) {
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
}

const ndjson = (...chunks) =>
  new Response(streamOf(...chunks), { status: 200, headers: { 'Content-Type': 'application/x-ndjson' } });
const line = (record) => JSON.stringify(record) + '\n';
const ask = (options) => askConversation('p1', 'c1', 'When did it start?', 'source_library', null, '', options);

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock.mockReset());
});
afterEach(() => {
  vi.unstubAllGlobals();
});

describe('askConversation', () => {
  it('requests a progress stream on the existing exchange endpoint', async () => {
    fetchMock.mockResolvedValue(ndjson(line({ type: 'answer', answer: CORRECTED, citations: CITATIONS })));

    await ask();

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/projects/p1/conversations/c1/exchanges');
    expect(init.method).toBe('POST');
    expect(init.headers.Accept).toContain('application/x-ndjson');
  });

  it('S-004: returns only the corrected answer and its citations from a plain JSON response', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ answer: CORRECTED, citations: CITATIONS }), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    const onStatus = vi.fn();

    const result = await ask({ onStatus });

    expect(result).toEqual({ answer: CORRECTED, citations: CITATIONS });
    expect(onStatus).not.toHaveBeenCalled();
  });

  it('S-004: returns only the corrected answer and its citations from a stream', async () => {
    fetchMock.mockResolvedValue(ndjson(line({ type: 'answer', answer: CORRECTED, citations: CITATIONS })));

    expect(await ask()).toEqual({ answer: CORRECTED, citations: CITATIONS });
  });

  it('S-007: reports the progress message once and then resolves with the final answer', async () => {
    const answer = line({ type: 'answer', answer: CORRECTED, citations: CITATIONS });
    // Split the records across chunks to cover partial lines.
    const status = line({ type: 'status', message: PROGRESS });
    fetchMock.mockResolvedValue(ndjson(status.slice(0, 12), status.slice(12) + answer.slice(0, 20), answer.slice(20)));
    const onStatus = vi.fn();

    const result = await ask({ onStatus });

    expect(onStatus).toHaveBeenCalledTimes(1);
    expect(onStatus).toHaveBeenCalledWith(PROGRESS);
    expect(result).toEqual({ answer: CORRECTED, citations: CITATIONS });
  });

  it.each(['json', 'stream'])('S-018: preserves the optional draft separately in %s', async (format) => {
    const payload = { answer: 'Checking timed out.', citations: [], unverified_draft: 'The pilot ended in July.' };
    const onStatus = vi.fn();
    const response = format === 'stream'
      ? ndjson(line({ type: 'status', message: PROGRESS }), line({ type: 'answer', ...payload }))
      : new Response(JSON.stringify(payload), { status: 201, headers: { 'Content-Type': 'application/json' } });
    fetchMock.mockResolvedValue(response);

    expect(await ask({ onStatus })).toEqual(payload);
    expect(onStatus.mock.calls).toEqual(format === 'stream' ? [[PROGRESS]] : []);
  });

  it('S-011: rejects with the server message when the stream ends in an error record', async () => {
    const message = 'I couldn’t finish checking this answer. Please try again.';
    fetchMock.mockResolvedValue(ndjson(line({ type: 'error', error: message })));

    await expect(ask()).rejects.toThrow(message);
  });

  it('S-011: keeps the status and code on a plain JSON error', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ error: 'The assistant couldn’t answer right now.', code: 'assistant.model_error' }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(ask()).rejects.toMatchObject({ status: 502, code: 'assistant.model_error' });
  });

  it('rejects when the stream ends without a terminal record', async () => {
    fetchMock.mockResolvedValue(ndjson(line({ type: 'status', message: PROGRESS })));

    await expect(ask()).rejects.toThrow();
  });
});
