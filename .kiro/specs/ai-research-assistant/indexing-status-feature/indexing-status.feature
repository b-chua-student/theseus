Feature: Manuscript indexing status
  A project member can check whether a manuscript is indexed and searchable.

  Background:
    Given a project with a manuscript

  @S-007 @criterion-5 @criterion-6
  Scenario: Checking the status of an indexed manuscript
    Given I am signed in as a member of the project
    And the manuscript has been saved and indexed
    When I check the indexing status of the manuscript
    Then I see its status and chunk count
    And its searchable flag is true
    And the assistant can retrieve from the manuscript

  @S-008 @criterion-5 @criterion-6
  Scenario: Checking the status of a manuscript never indexed
    Given I am signed in as a member of the project
    And the manuscript has never been saved or indexed
    When I check the indexing status of the manuscript
    Then its status is not_indexed
    And its searchable flag is false

  @S-009 @edge @criterion-7
  Scenario: A non-member cannot check the status
    Given I am signed in but not a member of the project
    When I check the indexing status of the manuscript
    Then the request is rejected with status 404

  @S-010 @edge @criterion-7
  Scenario: Checking the status of an unknown manuscript
    Given I am signed in as a member of the project
    When I check the indexing status of a manuscript that does not exist
    Then the request is rejected with status 404

  @S-011 @edge @criterion-7
  Scenario: Checking the status without a session
    Given I am not signed in
    When I check the indexing status of the manuscript
    Then the request is rejected with status 401
