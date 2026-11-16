Feature: Project Creation
  As an academic writer
  I want to organize my manuscripts into projects
  So that I can manage my research documentation effectively

  @S-001 @criterion-1
  Scenario: Successfully create a new project
    Given I am on the project creation dashboard
    When I submit valid project details
    Then the system SHALL create and save the project record successfully