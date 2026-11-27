# Writing assistant and evaluation

The assistant answers questions using selected manuscript and source-library context. The backend retrieves relevant indexed text, assembles prompts with bounded context, and invokes Gemini when configured. MongoDB deployments use local MiniLM embeddings and persistent Chroma storage by default.

Prompt construction delimits source text and manuscript content. The backend checks answers against available evidence when validation is enabled, processes results into structured answer and validation fields, and exposes those fields through JSON or NDJSON. The validation path can return pending or unverified results when its time budget expires. See [prompt guardrail tests](../backend/tests/domain/assistant/test_prompt_guardrails.py) and [exchange validation tests](../backend/tests/domain/assistant/api/test_exchange_validation_routes.py).

## Evaluation evidence

- The recorded production RAG baseline had 7 failed and 4 passed cases. A later verification at revision `eae281c` recorded 19 passing cases covering chunking, retrieval, persistence, and removal. The verification used local encoding and blocked outbound calls. [Baseline](../specs/assistant/production-rag/baseline.md) · [Verification](../specs/assistant/production-rag/verification.md)
- The [combined-context evaluator](../scripts/eval_combined_context.py) provides a separate check. Record the evaluated revision, model configuration, command, results, and failure examples when rerunning it.

Retrieved passages can be incomplete, unavailable, or stale during indexing. Retrieval tests at a historical revision measure specific behaviors. Live answer quality and production provider reliability require separate evidence.
