@S-001 @criterion-1
Feature: Create Project
  As an academic writer
  I want to organize my manuscripts into projects
  So that I can manage my research documentation effectively

  Scenario: Successfully create a project
    Given I am on the project creation dashboard
    When I submit valid project details
    Then the system SHALL create and save the project record successfully