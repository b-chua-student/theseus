/**
 * Minimal Gherkin reader and step binder for Vitest.
 *
 * Supports what the repository's feature files use: Feature, Background, Scenario,
 * Scenario Outline with Examples tables, tags, and Given/When/Then/And/But steps.
 * Outline rows are expanded into one scenario each, with `<placeholder>` values substituted.
 * And/But steps take the keyword of the step before them.
 */

const STEP = /^(Given|When|Then|And|But)\s+(\S.*)$/;
const SCENARIO = /^(Scenario Outline|Scenario Template|Scenario|Example):\s*(\S.*)$/;

/** @typedef {{ keyword: 'Given' | 'When' | 'Then', text: string }} Step */

const cells = (line) => line.trim().replace(/^\||\|$/g, '').split('|').map((cell) => cell.trim());

/**
 * Parse feature text into expanded scenarios.
 * @param {string} text
 * @returns {{ name: string, tags: string[], steps: Step[] }[]}
 */
export function parseFeature(text) {
  /** @type {Step[]} */
  const background = [];
  /** @type {{ name: string, tags: string[], steps: Step[], outline: boolean, examples: string[][] }[]} */
  const raw = [];
  /** @type {string[]} */
  let pendingTags = [];
  /** @type {'none' | 'background' | 'scenario' | 'examples'} */
  let mode = 'none';
  /** @type {Step['keyword']} */
  let keyword = 'Given';

  for (const source of text.split(/\r?\n/)) {
    const line = source.trim();
    if (!line || line.startsWith('#')) continue;
    if (line.startsWith('@')) {
      pendingTags.push(...line.split(/\s+/).map((tag) => tag.slice(1)));
      continue;
    }
    if (line.startsWith('Background:')) {
      mode = 'background';
      continue;
    }
    const scenario = SCENARIO.exec(line);
    if (scenario) {
      const outline = scenario[1] === 'Scenario Outline' || scenario[1] === 'Scenario Template';
      raw.push({ name: scenario[2], tags: pendingTags, steps: [], outline, examples: [] });
      pendingTags = [];
      mode = 'scenario';
      continue;
    }
    if (line.startsWith('Examples:')) {
      mode = 'examples';
      continue;
    }
    const step = STEP.exec(line);
    if (step && (mode === 'background' || mode === 'scenario')) {
      if (step[1] !== 'And' && step[1] !== 'But') keyword = /** @type {Step['keyword']} */ (step[1]);
      (mode === 'background' ? background : raw[raw.length - 1].steps).push({ keyword, text: step[2] });
    } else if (line.startsWith('|') && mode === 'examples') {
      raw[raw.length - 1].examples.push(cells(line));
    }
  }

  return raw.flatMap((scenario) => {
    const steps = [...background, ...scenario.steps];
    if (!scenario.outline) return [{ name: scenario.name, tags: scenario.tags, steps }];
    const [header, ...rows] = scenario.examples;
    return rows.map((row) => {
      const fill = (text) => header.reduce((out, key, index) => out.replaceAll(`<${key}>`, row[index]), text);
      return {
        name: `${scenario.name} [${row.join(', ')}]`,
        tags: scenario.tags,
        steps: steps.map((step) => ({ keyword: step.keyword, text: fill(step.text) })),
      };
    });
  });
}

/**
 * Find the single definition that matches a step's keyword and full text.
 * @template C
 * @param {[Step['keyword'], RegExp, (ctx: C, ...args: string[]) => unknown][]} definitions
 * @param {Step} step
 */
export function findStep(definitions, step) {
  const matches = definitions
    .filter(([keyword]) => keyword === step.keyword)
    .map(([, pattern, run]) => ({ match: new RegExp(`^(?:${pattern.source})$`).exec(step.text), run }))
    .filter((candidate) => candidate.match);
  const label = `${step.keyword} ${step.text}`;
  if (matches.length === 0) throw new Error(`Missing step definition: ${label}`);
  if (matches.length > 1) throw new Error(`Ambiguous step definition (${matches.length} matches): ${label}`);
  const [{ match, run }] = matches;
  return { run, args: match.slice(1) };
}
