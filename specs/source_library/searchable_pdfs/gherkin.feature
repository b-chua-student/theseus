Feature: Searchable PDFs
  Researchers can retrieve text from uploaded PDFs.

  @S-001 @criterion-1
  Scenario: Retrieve a matching passage from a PDF
    Given a searchable PDF has been uploaded to the Source Library
    When a researcher submits a query about text in the PDF
    Then the matching passage is retrieved
    And its page is returned when available

  @S-002 @criterion-2
  Scenario: Retrieve PDF text through Assistant questions
    Given a searchable PDF has been uploaded to the Source Library
    When a researcher asks the Assistant about text in the PDF
    Then the matching passage is retrieved
    And its page is returned when available
