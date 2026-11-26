Feature: Source Library PDF Upload
  Allow Theseus users to upload PDF documents to the Source Library.

  @S-001 @criterion-1
  Scenario: Successfully upload a PDF
    Given a Theseus user has a PDF document
    When the user uploads the PDF to the Source Library
    Then the PDF is successfully added to the Source Library

  @S-002 @criterion-2
  Scenario: Display the uploaded PDF in the library
    Given a Theseus user has successfully uploaded a PDF
    When the user opens the Source Library
    Then the uploaded PDF appears in the Source Library
