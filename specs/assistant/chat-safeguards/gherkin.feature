Feature: Assistant Input Guardrails, Chat Rate Limit, and History Cap
  Block direct injection inputs, limit chat bursts, and cap forwarded history.

  @S-010 @criterion-1
  Scenario: Direct rule-override attempt is blocked before calling the model
    Given a writer has an active conversation with the assistant
    When an evaluator submits a direct instruction-override prompt
    Then the request is rejected with a prompt-injection error
    And the chat model is not called

  @S-011 @criterion-1
  Scenario: Direct system-prompt disclosure attempt is blocked before calling the model
    Given a writer has an active conversation with the assistant
    When an evaluator submits a direct request to reveal internal system instructions
    Then the request is rejected with a prompt-injection error
    And the chat model is not called

  @S-012 @criterion-2
  Scenario: Burst chat submissions exceeding the per-minute limit are rejected
    Given chat rate limiting is enabled for the assistant
    And a writer has already reached the per-minute limit for chat questions
    When the writer submits another question within the same minute
    Then the request is rejected with a rate-limit error

  @S-013 @criterion-3
  Scenario: Long conversations forward only the most recent exchanges to the model
    Given a conversation has more completed exchanges than the default history cap
    When the writer asks a follow-up question
    Then only the most recent completed exchanges within the cap are forwarded in order
    And all earlier exchanges remain stored in the conversation

  @S-014 @criterion-4
  Scenario: Automated safeguard checks run offline without live credentials
    Given the automated test suite runs without network access or live external credentials
    When the assistant safeguard tests are executed
    Then input blocking, burst rate limiting, and history capping are verified offline

  @S-015 @criterion-1 @edge
  Scenario: Benign academic questions about prompt injection are allowed
    Given a writer has an active conversation with the assistant
    When the writer asks an academic question explaining how prompt injection works
    Then the question is forwarded to the chat model
    And the writer receives an answer

  @S-016 @criterion-1 @edge
  Scenario: Rejected prompt-injection attempts are not saved in conversation history
    Given a writer has an active conversation with one prior completed exchange
    When an evaluator submits a direct instruction-override prompt
    Then the request is rejected with a prompt-injection error
    And the conversation history still contains only the prior completed exchange

  @S-017 @criterion-3 @edge
  Scenario: Conversations within the history cap forward all completed exchanges
    Given a conversation has fewer completed exchanges than the default history cap
    When the writer asks a follow-up question
    Then every completed exchange is forwarded to the model in chronological order
