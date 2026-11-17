Feature: Source indexing
  Added sources are indexed and removed sources are de-indexed so the assistant stays in sync with the library.

  Background:
    Given a project with a library of sources

  @S-004 @criterion-4
  Scenario: An added source is indexed
    When a source is added to the library
    Then the content of the source is indexed

  @S-005 @criterion-4
  Scenario: A removed source is de-indexed
    Given a source whose content is indexed
    When the source is removed from the library
    Then the content of the source is removed from the index

  @S-006 @edge @criterion-3
  Scenario: A failure on one source does not affect other changes
    Given indexing of a source has failed
    When another source is added to the library
    Then the content of the other source is indexed

  @S-028 @edge @criterion-3
  Scenario: A failed de-indexing does not affect other changes
    Given de-indexing of a source has failed
    When another source is removed from the library
    Then the content of the other source is removed from the index
