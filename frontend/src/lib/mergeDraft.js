export const conflictKey = (conflict) => JSON.stringify([conflict.section_heading, conflict.field]);

export function carryOverChoices(previous, conflicts) {
  return Object.fromEntries(conflicts.map(conflictKey).filter(key => previous[key])
    .map(key => [key, previous[key]]));
}

export function toResolutions(conflicts, choices) {
  return conflicts.map(c => ({ section_id: c.section_id, field: c.field, choice: choices[conflictKey(c)] }));
}

export function valuePreview(field, value) {
  if (value === null) return 'Deleted / none';
  if (field === 'body') {
    try {
      const text = node => typeof node?.text === 'string' ? node.text : (node?.content ?? []).map(text).join(' ');
      return text(JSON.parse(value)).slice(0, 200);
    } catch { return String(value).slice(0, 200); }
  }
  return (typeof value === 'object' ? JSON.stringify(value) : String(value)).slice(0, 200);
}

export function mergeDisabledReason(started, count, busy) {
  return !started ? 'Draft tracking has not started' : count < 2 ? 'At least two drafts are required'
    : busy ? 'A draft operation is in progress' : '';
}
