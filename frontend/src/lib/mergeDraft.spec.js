import { describe, it, expect } from 'vitest';
import { conflictKey, carryOverChoices, toResolutions, valuePreview, mergeDisabledReason } from './mergeDraft.js';

describe('merge helpers', () => {
  it('carries matching choices and serializes resolutions', () => {
    const c = { section_id: 'a', section_heading: 'Introduction', field: 'body' };
    const choices = { [conflictKey(c)]: 'source', old: 'target' };
    expect(carryOverChoices(choices, [c])).toEqual({ [conflictKey(c)]: 'source' });
    expect(toResolutions([c], choices)).toEqual([{ section_id: 'a', field: 'body', choice: 'source' }]);
  });
  it('previews body text safely and truncates it', () => {
    expect(valuePreview('body', JSON.stringify({content:[{text:'hello'}]}))).toBe('hello');
    expect(valuePreview('body', 'x'.repeat(300))).toHaveLength(200);
  });
  it.each([[false,2,false,'Draft tracking has not started'],[true,1,false,'At least two drafts are required'],[true,2,true,'A draft operation is in progress'],[true,2,false,'']])('checks button state %s %s %s', (started,count,busy,reason) => {
    expect(mergeDisabledReason(started,count,busy)).toBe(reason);
  });
});
