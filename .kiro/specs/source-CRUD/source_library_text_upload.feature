@source-library @text-upload
Feature: Source Library Text Upload
  As a user
  I want to upload text content directly to the source library
  So that the system can use it as grounding reference material

  Background:
    Given I am an authenticated user
    And I am on the source library text upload page

  # ---------------------------------------------------------------------------
  # Create
  # ---------------------------------------------------------------------------

  @create @smoke
  Scenario: Upload text with required fields only
    When I enter the title "API Spec v1"
    And I enter the content "GET /users returns a list of users."
    And I click "Save"
    Then the text content is saved successfully
    And I see a success message
    And the content has version 1
    And the content is active
    And the content type defaults to "other"

  @create
  Scenario: Upload text with all metadata
    When I enter the title "Sprint Planning Notes"
    And I enter the description "Notes from sprint 12 planning"
    And I enter the tags "sprint, planning, q3"
    And I select the content type "notes"
    And I enter the content "Decided to prioritize search performance."
    And I click "Save"
    Then the text content is saved successfully
    And the content has the tags "sprint", "planning" and "q3"
    And the content type is "notes"

  @create @validation
  Scenario: Reject empty content
    When I enter the title "Empty Doc"
    And I leave the content empty
    And I click "Save"
    Then the content is not saved
    And I see the error "Content is required"

  @create @validation
  Scenario: Reject missing title
    When I leave the title empty
    And I enter the content "Some content"
    And I click "Save"
    Then the content is not saved
    And I see the error "Title is required"

  @create @validation
  Scenario Outline: Enforce content length limits
    When I enter the title "Length Test"
    And I enter content of <length> characters
    And I click "Save"
    Then the result is "<result>"

    Examples:
      | length  | result                                   |
      | 1       | saved                                    |
      | 100000  | saved                                    |
      | 100001  | rejected with "Content exceeds 100,000"  |

  @create @validation
  Scenario Outline: Enforce metadata limits
    When I enter the title "Metadata Test"
    And I enter the content "Valid content"
    And I set <field> to a value of <length> characters
    And I click "Save"
    Then the result is "<result>"

    Examples:
      | field       | length | result                                    |
      | title       | 200    | saved                                     |
      | title       | 201    | rejected with "Title exceeds 200"         |
      | description | 1000   | saved                                     |
      | description | 1001   | rejected with "Description exceeds 1000"  |

  @create @validation
  Scenario Outline: Enforce tag limit
    When I enter the title "Tag Test"
    And I enter the content "Valid content"
    And I enter <count> comma-separated tags
    And I click "Save"
    Then the result is "<result>"

    Examples:
      | count | result                              |
      | 10    | saved                               |
      | 11    | rejected with "Maximum 10 tags"     |

  @create @validation
  Scenario: Reject invalid content type
    When I submit a create request with content type "spreadsheet"
    Then the API responds with status 400
    And the error lists the allowed content types "documentation", "notes", "code" and "other"

  @create
  Scenario: Preserve UTF-8 characters
    When I enter the title "Unicode Test"
    And I enter the content "Héllo 世界 🌏 مرحبا"
    And I click "Save"
    Then the text content is saved successfully
    And retrieving the content returns "Héllo 世界 🌏 مرحبا" unchanged

  @create @ui
  Scenario: Character counter updates as I type
    When I enter the content "Hello"
    Then the character counter shows "5 / 100,000"

  @create @ui
  Scenario: Preview content before saving
    Given I have entered a title and content
    When I click "Preview"
    Then I see a read-only preview of the content
    And the content is not yet saved
    When I click "Save" from the preview
    Then the text content is saved successfully

  @create @ui
  Scenario: Draft is auto-saved
    Given I have entered a title and partial content
    When I leave the page and return
    Then my draft title and content are restored

  # ---------------------------------------------------------------------------
  # Read / List
  # ---------------------------------------------------------------------------

  @read
  Scenario: View a specific text content item
    Given I have uploaded text content titled "API Spec v1"
    When I open "API Spec v1"
    Then I see its title, description, tags, content type, content and timestamps

  @read
  Scenario: List my text content with pagination
    Given I have uploaded 25 text content items
    When I view the content management page
    Then I see the first page of items in a card layout
    And I can navigate to the next page

  @read @filter
  Scenario Outline: Filter the list
    Given I have uploaded items with various tags and content types
    When I filter by <filter> "<value>"
    Then I only see items matching that <filter>

    Examples:
      | filter       | value         |
      | content type | code          |
      | tag          | api           |

  @read @sort
  Scenario Outline: Sort the list
    Given I have uploaded multiple text content items
    When I sort by <sort>
    Then the items are ordered by <sort>

    Examples:
      | sort  |
      | date  |
      | title |

  @read @security
  Scenario: Cannot view another user's content
    Given another user has uploaded text content
    When I request that content by its id
    Then the API responds with status 404 or 403

  @read
  Scenario: Request a non-existent item
    When I request text content with an unknown id
    Then the API responds with status 404

  # ---------------------------------------------------------------------------
  # Update and versioning
  # ---------------------------------------------------------------------------

  @update @versioning
  Scenario: Edit content increments version
    Given I have uploaded text content at version 1
    When I change the content and click "Save"
    Then the content is updated
    And the version is 2
    And updatedAt is later than createdAt

  @update
  Scenario: Edit metadata only
    Given I have uploaded text content
    When I change the tags and save
    Then the tags are updated
    And the original content is unchanged

  @update @validation
  Scenario: Updates follow the same validation rules as create
    Given I have uploaded text content
    When I clear the title and save
    Then the update is rejected with "Title is required"
    And the stored content is unchanged

  @update @security
  Scenario: Cannot update another user's content
    Given another user has uploaded text content
    When I send an update request for that content
    Then the API responds with status 404 or 403
    And the content is unchanged

  # ---------------------------------------------------------------------------
  # Delete
  # ---------------------------------------------------------------------------

  @delete
  Scenario: Soft delete content
    Given I have uploaded text content titled "Old Notes"
    When I delete "Old Notes" and confirm
    Then the content is marked inactive
    And "Old Notes" no longer appears in my list
    And "Old Notes" is excluded from search results
    And the record is retained in storage

  @delete
  Scenario: Cancel deletion
    Given I have uploaded text content titled "Old Notes"
    When I choose to delete "Old Notes" and cancel
    Then the content remains active

  @delete @security
  Scenario: Cannot delete another user's content
    Given another user has uploaded text content
    When I send a delete request for that content
    Then the API responds with status 404 or 403
    And the content remains active

  # ---------------------------------------------------------------------------
  # Search
  # ---------------------------------------------------------------------------

  @search
  Scenario: Search by keyword in content
    Given I have uploaded text content containing "rate limiting"
    When I search for "rate limiting"
    Then the matching item appears in the results

  @search
  Scenario Outline: Search matches multiple fields
    Given I have uploaded an item with <field> "<text>"
    When I search for "<text>"
    Then the item appears in the results

    Examples:
      | field       | text         |
      | title       | onboarding   |
      | description | quarterly    |
      | tag         | architecture |

  @search
  Scenario: Search with no matches
    When I search for "zzzz-no-match"
    Then I see an empty results message

  @search @filter
  Scenario: Search combined with filters
    Given I have uploaded notes and code items that both contain "auth"
    When I search for "auth" and filter by content type "code"
    Then I only see code items

  @search @security
  Scenario: Search only returns my own content
    Given another user has uploaded content containing "confidential"
    When I search for "confidential"
    Then I do not see the other user's content

  # ---------------------------------------------------------------------------
  # Source library integration
  # ---------------------------------------------------------------------------

  @integration
  Scenario: Uploaded text appears in the source library
    Given I have uploaded text content titled "API Spec v1"
    When I open the source library
    Then "API Spec v1" is listed as a source

  @integration @grounding
  Scenario: Uploaded text is used for grounding
    Given I have uploaded text content describing the "GET /users" endpoint
    When I ask the system a question about the "GET /users" endpoint
    Then the response is grounded in my uploaded content

  @integration @grounding
  Scenario: Deleted content is not used for grounding
    Given I have deleted text content describing the "GET /users" endpoint
    When I ask the system a question about the "GET /users" endpoint
    Then the response does not reference the deleted content

  # ---------------------------------------------------------------------------
  # Security
  # ---------------------------------------------------------------------------

  @security @auth
  Scenario Outline: Unauthenticated requests are rejected
    Given I am not authenticated
    When I send a <method> request to "<endpoint>"
    Then the API responds with status 401

    Examples:
      | method | endpoint                |
      | POST   | /api/sources/text       |
      | GET    | /api/sources/text       |
      | GET    | /api/sources/text/{id}  |
      | PUT    | /api/sources/text/{id}  |
      | DELETE | /api/sources/text/{id}  |
      | GET    | /api/sources/text/search|

  @security @xss
  Scenario: Script content is sanitized
    When I enter the title "XSS Test"
    And I enter the content "<script>alert('xss')</script>"
    And I click "Save"
    And I view the content
    Then the script is not executed
    And the content is displayed as inert text

  @security @injection
  Scenario: Injection attempts are neutralized
    When I search for "'; DROP TABLE text_content; --"
    Then the search completes without error
    And no data is modified

  @security @rate-limit
  Scenario: Rate limiting on uploads
    Given I have exceeded the upload rate limit
    When I send another create request
    Then the API responds with status 429
    And the response indicates when I can retry

  # ---------------------------------------------------------------------------
  # Non-functional
  # ---------------------------------------------------------------------------

  @performance
  Scenario: Upload responds quickly for small content
    When I upload 10KB of text content
    Then the API responds in under 2 seconds

  @performance
  Scenario: Search responds quickly at scale
    Given the library contains 1000 text documents
    When I search for a keyword
    Then the API responds in under 1 second

  @performance @concurrency
  Scenario: Multiple users upload concurrently
    Given 20 users upload text content at the same time
    Then all uploads succeed
    And each user only sees their own content

  @storage
  Scenario: Large content is stored and retrieved intact
    When I upload 100,000 characters of text content
    Then retrieving the content returns the exact original text

  @accessibility @ui
  Scenario: Upload interface is accessible
    When I navigate the text upload page using only the keyboard
    Then all fields and buttons are reachable
    And form fields have associated labels
    And error messages are announced to screen readers

  @responsive @ui
  Scenario Outline: Interface adapts to screen size
    Given my viewport is <device>
    When I open the text upload page
    Then the layout is usable without horizontal scrolling

    Examples:
      | device  |
      | mobile  |
      | tablet  |
      | desktop |
