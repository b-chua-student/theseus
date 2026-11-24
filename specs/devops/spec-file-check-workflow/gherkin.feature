Feature: Check spec files during pull request review
  Contributors receive feedback on structural and traceability errors in spec files.

  @S-012 @criterion-1 @criterion-9
  Scenario: Conforming spec files pass review checks
    Given a pull request adds or changes spec files that conform to the repository templates
    When the pull request is checked
    Then the spec check passes
    And the existing intake and Gherkin checks are available

  @S-013 @criterion-7 @edge
  Scenario: Legacy spec errors outside affected features do not cause failures
    Given a pull request changes conforming spec files in one feature directory
    And an unrelated feature directory contains nonconforming legacy spec files
    When the pull request is checked
    Then the spec check passes

  @S-014 @criterion-8 @edge
  Scenario Outline: Changes without a spec file do not trigger spec validation
    Given a pull request changes only <file>
    When the pull request is checked
    Then the spec check does not run

    Examples:
      | file                |
      | a spec template     |
      | a source ticket     |
      | a Gherkin file      |

  @S-015 @criterion-2 @criterion-6 @edge
  Scenario Outline: Structural errors fail the spec check
    Given a pull request adds or changes a spec file that contains <error>
    When the spec check runs
    Then the spec check fails
    And the failure identifies the affected file and the rule that failed

    Examples:
      | error                                  |
      | a missing required heading             |
      | a missing required table column        |
      | a malformed requirement ID             |
      | a duplicate requirement ID in its table |
      | a malformed design ID                  |
      | a duplicate design ID in its table      |
      | a malformed task ID                    |
      | a duplicate task ID in its table        |

  @S-016 @criterion-3 @criterion-6 @edge
  Scenario Outline: Invalid requirement references fail the spec check
    Given a pull request adds or changes a requirements file with a requirement that <error>
    When the spec check runs
    Then the spec check fails
    And the failure identifies the affected file and the rule that failed

    Examples:
      | error                             |
      | lacks its source ticket reference |
      | cites a nonexistent ticket line   |
      | cites a blank ticket line         |
      | references an unknown scenario    |

  @S-017 @criterion-4 @criterion-6 @edge
  Scenario Outline: Invalid or missing traceability fails the spec check
    Given a pull request adds or changes spec files in a feature where <error>
    When the spec check runs
    Then the spec check fails
    And the failure identifies the affected file and the rule that failed

    Examples:
      | error                                     |
      | a design decision has an invalid reference |
      | a task has an invalid reference            |
      | a requirement has no design decision      |
      | a design decision has no task             |
      | a scenario has no verification task       |

  @S-018 @criterion-5 @criterion-6 @edge
  Scenario Outline: Inconsistent task dependencies fail the spec check
    Given a pull request adds or changes a tasks file where <error>
    When the spec check runs
    Then the spec check fails
    And the failure identifies the affected file and the rule that failed

    Examples:
      | error                                                   |
      | the task graph and table disagree                       |
      | task dependencies contain a cycle                      |
      | an independent task is outside wave 1                  |
      | a dependent task is outside the wave after its latest prerequisite |

  @S-019 @criterion-11
  Scenario Outline: Valid revision inputs select changes
    Given conforming spec files changed in the comparison selected by <revision inputs>
    When the spec check runs with those revision inputs
    Then the spec check passes and reports the affected feature

    Examples:
      | revision inputs               |
      | a valid base revision only    |
      | valid base and head revisions |

  @S-020 @criterion-10 @edge
  Scenario Outline: Option-like revision inputs are rejected
    Given an option-like value is supplied as the <revision> revision
    When the spec check runs with those revision inputs
    Then the spec check fails and identifies the invalid revision input

    Examples:
      | revision |
      | base     |
      | head     |
