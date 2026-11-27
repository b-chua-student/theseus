Feature: Production RAG Pipeline, Local Embeddings, and Vector Cleanup
  Use overlapping chunking, local embeddings, persistent vectors, and cleanup.

  @S-019 @criterion-1
  Scenario: Long document text is split into ordered overlapping chunks with hashes
    Given a document contains multiple paragraphs of prose exceeding one chunk size
    When the production document chunker splits the document text
    Then multiple ordered chunks are produced with sequential positions and content hashes
    And adjacent chunks preserve contextual overlap across chunk boundaries

  @S-020 @criterion-2
  Scenario: Local semantic embeddings are generated without external API calls
    Given a list of ordered document chunks is ready for indexing
    When the local embedding generator produces embeddings for the chunks
    Then one fixed-dimension vector is returned for each chunk in the same order
    And no external AI provider API call is made

  @S-021 @criterion-3
  Scenario: Production startup wires real chunking, local embeddings, and persistent vectors
    Given the application starts in production mode with persistent storage configured
    When the assistant module dependencies are assembled
    Then the production chunker, local embedding generator, and persistent vector store are wired

  @S-022 @criterion-4
  Scenario: Removing an indexed source deletes its vectors from the vector store
    Given a project source has been indexed and stored in the vector store
    When the source is removed from the source library
    Then the indexed document record is marked stale
    And all vectors for that source are deleted from the vector store

  @S-023 @criterion-5
  Scenario: Automated RAG pipeline checks run offline without live credentials
    Given the automated test suite runs without network access or live external credentials
    When the production RAG pipeline tests are executed
    Then chunking, local embeddings, wiring, and vector cleanup are verified offline

  @S-024 @criterion-1 @edge
  Scenario: Blank or whitespace-only text produces no chunks
    Given a document contains only whitespace characters
    When the production document chunker splits the document text
    Then an empty list of chunks is returned

  @S-025 @criterion-3 @edge
  Scenario: Test startup preserves in-memory defaults without persistent vector storage
    Given the application starts in automated testing mode
    When the assistant module dependencies are assembled
    Then the in-memory chunker, embedding generator, and vector store defaults remain active

  @S-026 @criterion-4 @edge
  Scenario: Removing a source that was never indexed does not fail vector cleanup
    Given a project source has never been indexed in the assistant
    When the source is removed from the source library
    Then the removal handler completes without error
