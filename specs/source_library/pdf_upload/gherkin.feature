Feature: Source Library PDF Upload
  Allow Theseus users to upload PDF documents to the Source Library.

  @S-001 @criterion-1
  Scenario: Successfully upload a PDF
    Given a Theseus user has a PDF document
    When the user uploads the PDF to the Source Library
    Then the uploaded PDF appears in the Source Library

  @S-002 @criterion-1
  Scenario: View an uploaded PDF in the Source Library
    Given a Theseus user has uploaded a PDF document
    When the user opens the Source Library
    Then the uploaded PDF is displayed
