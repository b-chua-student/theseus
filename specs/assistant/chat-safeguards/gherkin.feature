Feature: Assistant Input Guardrails, Chat Rate Limit, and History Cap
  Block direct injection inputs, limit chat bursts, and cap forwarded history.

  @S-015 @criterion-1
  Scenario Outline: Benign academic questions about AI security are allowed
    Given a writer has an active conversation with the assistant
    When the writer asks an academic question about <topic>
    Then the question is forwarded to the chat model
    And the writer receives an answer

    Examples:
      | topic            |
      | prompt injection |
      | system prompts   |

  @S-018 @criterion-2
  Scenario: Automated runs accept a burst by default
    Given an automated run uses the default test settings
    When a writer submits eleven ordinary questions within the same minute
    Then all eleven questions receive answers

  @S-014 @criterion-4
  Scenario: Automated safeguard checks run offline without live credentials
    Given the automated test suite runs without network access or live external credentials
    When the assistant safeguard tests are executed
    Then input blocking, benign pass-through, burst rate limiting, and history capping are verified offline

  @S-010 @criterion-1 @edge
  Scenario: Direct rule-override attempt is blocked before calling the model
    Given a writer has an active conversation with the assistant
    When an evaluator submits a direct instruction-override prompt
    Then the request is rejected with a prompt-injection error
    And the chat model is not called

  @S-011 @criterion-1 @edge
  Scenario: Direct system-prompt disclosure attempt is blocked before calling the model
    Given a writer has one prior completed exchange in the conversation
    When an evaluator submits a direct request to reveal internal system instructions
    Then the request is rejected with a prompt-injection error
    And the chat model is not called
    And the prior exchange is still the only stored exchange
    And no exchange is pending

  @S-012 @criterion-2 @edge
  Scenario: Burst chat submissions exceeding the per-minute limit are rejected
    Given chat rate limiting is enabled for the assistant
    And the writer has made no recent submissions
    When the writer submits eleven ordinary questions within the same minute
    Then the first ten questions receive answers
    And the eleventh receives a rate-limit error without a model call for that question

  @S-013 @criterion-3 @edge
  Scenario: Long conversations forward only the most recent exchanges to the model
    Given a conversation has eleven completed exchanges numbered from oldest to newest
    When the writer asks a follow-up question
    Then only exchanges 2 through 11 are forwarded in chronological order
    And all eleven prior exchanges remain stored in the conversation

  @S-016 @criterion-1 @edge
  Scenario: Rejected prompt-injection attempts are not saved in conversation history
    Given a writer has an active conversation with one prior completed exchange
    When an evaluator submits a direct instruction-override prompt
    Then the request is rejected with a prompt-injection error
    And the conversation history still contains only the prior completed exchange
    And no exchange is pending

  @S-017 @criterion-3 @edge
  Scenario: Conversations within the history cap forward all completed exchanges
    Given a conversation has ten completed exchanges
    When the writer asks a follow-up question
    Then every completed exchange is forwarded to the model in chronological order
