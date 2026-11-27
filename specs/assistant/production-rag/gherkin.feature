Feature: Writers can retrieve relevant passages from their source library
  Writers can search indexed sources by meaning and remove sources from retrieval.

  @S-019 @criterion-1
  Scenario: Long document text is split into ordered overlapping chunks with hashes
    Given a document contains multiple paragraphs of prose exceeding the shared 192-content-token budget
    When the production document chunker splits the document text
    Then multiple ordered chunks are produced with sequential positions and content hashes
    And each chunk contains at most 192 content tokens
    And adjacent chunks share the 32 content tokens at their common boundary

  @S-020 @criterion-2
  Scenario: Local semantic embeddings are generated without external API calls
    Given a list of ordered document chunks is ready for indexing
    When the local embedding generator produces embeddings for the chunks
    Then one fixed-dimension vector is returned for each chunk in the same order
    And no external AI provider API call is made

  @S-021 @criterion-3
  Scenario: Indexed passages remain searchable after production restarts
    Given a source has been indexed in production using the local model
    When the application restarts with the same storage
    Then a writer can retrieve its matching passage without reindexing the source

  @S-022 @criterion-4
  Scenario: Removing an indexed source deletes its vectors from the vector store
    Given two sources in the same project have been indexed
    When one source is removed from the source library
    Then the removed source record is marked stale
    And all vectors for that source are deleted from the vector store
    And the other source remains retrievable

  @S-023 @criterion-5
  Scenario: Automated RAG pipeline checks run offline without live credentials
    Given the automated test suite runs without network access or live external credentials
    When the production RAG pipeline tests are executed
    Then chunking, local embeddings, wiring, and vector cleanup are verified offline

  @S-027 @criterion-2
  Scenario: A paraphrased question retrieves the passage with the matching meaning
    Given the local model is available and network access is disabled
    And passages about bicycle repair and bread baking have been indexed locally
    When a writer searches for "How can I fix a flat on my bike?"
    Then the bicycle repair passage ranks ahead of the bread baking passage
    And the query uses the same local embedding model as the indexed passages

  @S-024 @criterion-1 @edge
  Scenario: Blank or whitespace-only text produces no chunks
    Given a document contains only whitespace characters
    When the production document chunker splits the document text
    Then an empty list of chunks is returned

  @S-025 @criterion-3 @edge
  Scenario: A default test run indexes sources in memory
    Given the application starts with its default automated test settings
    When a source is indexed during the test run
    Then its chunks and embeddings are available for retrieval in memory
    And no data is written to production storage

  @S-026 @criterion-4 @edge
  Scenario: Removing a source that was never indexed does not fail vector cleanup
    Given a project source has never been indexed in the assistant
    When the source is removed from the source library
    Then the removal handler completes without error

  @S-028 @criterion-4 @edge
  Scenario: Removal takes effect even when indexing is underway
    Given indexing has started for a source
    When the source is removed while indexing is in progress
    Then after removal completes its index record is stale and its vectors are absent
    And those outcomes still hold once the indexing job finishes
