Feature: Project Verification
  As an academic writer
  I want to validate project inputs
  So that I avoid duplicate or invalid data entries

  @S-002 @criterion-2
  Scenario: Attempt to create a project with duplicate or invalid data
    Given I am on the project creation dashboard
    When I submit project data with missing required fields
    Then the system SHALL reject the creation request with a validation error