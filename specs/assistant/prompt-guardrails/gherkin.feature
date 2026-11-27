Feature: Assistant Prompt Guardrails and Safety Controls
  Enforce prompt-injection guardrails, data isolation, and safety defaults across scopes.

  @S-001 @criterion-1 @criterion-4
  Scenario: Default assistant configuration applies guardrails and safety filters
    Given the assistant chat provider is initialized without custom overrides
    When the assistant configuration is prepared for handling questions
    Then a default system instruction is active
    And the instruction enforces rule-override resistance, confidentiality, and honest grounding
    And the instruction directs the assistant to use manuscripts and retrieved excerpts as references and ignore instructions embedded in either
    And the default filters block content rated medium or high probability for harassment, hate speech, sexually explicit content, and dangerous content

  @S-002 @criterion-1
  Scenario: General questions remain allowed in none scope without fake document claims
    Given a writer asks a general question in none context scope
    When the assistant prepares the response using its default system instruction
    Then general questions are permitted without requiring attached documents
    And the instruction forbids claiming access to unattached manuscripts or sources

  @S-003 @criterion-2
  Scenario: Retrieved source excerpts are isolated from the user question
    Given a writer asks a question in source library scope
    And relevant source excerpts are retrieved for the project
    When the assistant builds the prompt for the model
    Then the retrieved source excerpts are enclosed in explicit untrusted-data boundaries
    And the user question is separated from the untrusted source block

  @S-004 @criterion-3
  Scenario: Manuscript text is isolated from the user question in manuscript scope
    Given a writer asks a question in manuscript scope with manuscript text
    When the assistant prepares the manuscript-scoped prompt
    Then the manuscript text is enclosed in explicit untrusted-data boundaries
    And the user question is separated from the untrusted manuscript block

  @S-005 @criterion-5
  Scenario: Automated guardrail checks run offline without live credentials
    Given the automated test suite runs without network access or live external model credentials
    When the assistant guardrail tests are executed
    Then the guardrail checks complete successfully
    And default system instructions and safety filter settings are verified
    And untrusted-data isolation for both sources and manuscripts is verified

  @S-009 @criterion-1
  Scenario Outline: Writers receive ordinary answers with default guardrails active
    Given a writer in <scope> scope has <context>
    And the model is set to return "<answer>"
    When the writer asks "<question>"
    Then the writer receives "<answer>"

    Examples:
      | scope          | context                                      | question                      | answer                       |
      | none           | no attachments                               | What is a primary source?     | A firsthand record.          |
      | manuscript     | a manuscript describing twelve interviews    | How many interviews are cited? | Twelve interviews.           |
      | source library | a retrieved excerpt naming the survey site   | Where was the survey held?    | At the university library.   |

  @S-006 @criterion-2 @edge
  Scenario: Embedded boundary-escape text inside a retrieved source is neutralized
    Given a retrieved source excerpt contains closing boundary markers and override instructions
    When the assistant builds the prompt for the model
    Then the embedded closing boundary markers inside the source text are neutralized
    And the source text remains contained inside the untrusted-data boundary

  @S-007 @criterion-3 @edge
  Scenario: Embedded boundary-escape text inside a manuscript is neutralized
    Given a manuscript contains closing boundary markers and override instructions
    When the assistant prepares the manuscript-scoped prompt
    Then the embedded closing boundary markers inside the manuscript text are neutralized
    And the manuscript text remains contained inside the untrusted-data boundary

  @S-008 @criterion-1 @edge
  Scenario: Direct override and prompt-disclosure attempts are constrained by defaults
    Given the assistant is initialized with its default system instruction
    When an evaluator submits an override or system-prompt disclosure attempt
    Then the active system instruction directs the assistant to refuse rule overrides
    And the active system instruction forbids disclosing internal instructions
