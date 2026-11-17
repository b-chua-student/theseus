Feature: Manuscript indexing
  A saved manuscript is indexed automatically so the assistant can answer questions about its latest content.

  Background:
    Given a project with a manuscript

  @S-001 @criterion-1
  Scenario: A saved manuscript becomes searchable
    Given the manuscript has just been saved
    When indexing of the manuscript completes
    Then the manuscript is marked as searchable
    And its chunk count is greater than zero

  @S-002 @criterion-2
  Scenario: Saving does not wait for indexing
    Given the manuscript has content
    When the manuscript is saved
    Then the save completes without waiting for indexing
    And the manuscript is queued for indexing

  @S-003 @edge @criterion-3
  Scenario: Failed indexing does not affect other manuscripts
    Given indexing of the manuscript has failed
    When another manuscript is saved
    Then the other manuscript is queued for indexing
    And the other manuscript is indexed when its turn comes
    And later changes continue to be processed
