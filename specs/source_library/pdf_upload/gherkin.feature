@S-001 @criterion-1
Feature: Source Library PDF Upload
  Allow Theseus users to upload PDF documents to the Source Library.

  Scenario: Successfully upload a PDF
    Given a Theseus user has a PDF document
    When the user uploads the PDF to the Source Library
    Then the uploaded PDF appears in the Source Library
