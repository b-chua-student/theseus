Feature: Project Management
  As an academic writer
  I want to create and validate my research projects
  So that I can organize my manuscripts without duplicate or invalid entries

  @S-001 @criterion-1
  Scenario: Successfully create a project
    Given I am on the project creation dashboard
    When I submit valid project details
    Then the system SHALL create and save the project record successfully

  @S-002 @edge @criterion-2
  Scenario: Attempt to create a project with duplicate or invalid data
    Given I am on the project creation dashboard
    When I submit project data with missing required fields
    Then the system SHALL reject the creation request with a validation error