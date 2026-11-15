# Repository Findings for Source Library Text Upload

## Project Overview
**Theseus** is a web-based document editor with Git-like version control and an AI research assistant. The text upload feature will extend the existing source library functionality.

## Architecture Context
- **Frontend**: Svelte 5, Vite, Tiptap rich-text editor
- **Backend**: Python 3.12, Flask, Pydantic, Flask-Limiter, Gunicorn  
- **Storage**: MongoDB (production), in-memory adapters (tests)
- **AI**: Google Gemini (chat), vector store capabilities via ChromaDB adapter

## Existing Source Library Structure

### Backend Domain (`backend/domain/src_lib/`)
```
src_lib/
├── api/                     # HTTP layer
│   ├── routes.py           # Existing REST endpoints
│   ├── requests.py         # Pydantic request models  
│   └── errors.py           # Domain-specific errors
├── models/                 # Business logic
│   ├── aggregates.py       # Source aggregate root
│   ├── value_objects.py    # Value objects
│   └── events.py          # Domain events
├── services/              # Use cases
│   └── ...               # Command/query handlers
└── infrastructure/        # Technical implementation
    ├── ports/            # Interfaces
    └── adapters/         # Implementations
```

### Current Source Model (`aggregates.py`)
```python
class Source:
    id: SourceId
    title: SourceTitle
    authors: tuple[Author, ...]  # Currently for bibliographic sources
    year: int | None             # Publication year
    file_ref: str                # File reference (e.g., path or URL)
    project_id: UUID
    removed_at: datetime | None  # Soft delete
```

**Key Observations:**
- Current model is bibliographic-focused (authors, year)
- Uses `file_ref` field for file storage reference
- No direct text content storage capability
- Soft delete via `removed_at` field
- Domain events: `SourceAdded`, `SourceRemoved`

### Current API Endpoints (`routes.py`)
- `GET /` - List all sources
- `POST /` - Add new source (requires `file_ref`)
- `GET /<source_id>` - Get specific source
- `DELETE /<source_id>` - Remove source (soft delete)
- `PATCH /<source_id>/metadata` - Update metadata

## Integration Points Identified

### 1. Authentication System
- Uses `@login_required` decorator from `domain.identity.api.auth.routes`
- Authentication already integrated into existing source endpoints

### 2. Dependency Injection
- Uses Flask extension container pattern: `current_app.extensions["container"]`
- Services accessed via `container.source.<operation>.execute()`

### 3. Assistant Integration
- **Files found**: `on_source_added.py`, `on_source_removed.py`, `ingestion_worker.py`
- **Existing ports**: `source_content_provider.py`
- **Implication**: Text uploads should trigger assistant content indexing

### 4. Search Infrastructure
- MongoDB with potential vector store integration (ChromaDB adapter exists)
- Search capabilities needed for text content

## Frontend Context
- **Framework**: Svelte 5
- **UI Library**: Likely custom components (need to explore `frontend/src/components/`)
- **API Client**: `frontend/src/lib/api/` - existing API communication patterns
- **Current State**: No text upload UI found, likely new development

## Database Considerations
- **Current**: MongoDB stores `Source` aggregates
- **Text Storage Options**:
  1. Extend existing `Source` model with text fields
  2. Create separate `TextContent` collection
  3. Hybrid: Use `file_ref` to reference text storage location

## Technical Constraints

### Validation Framework
- Uses Pydantic for request validation (see `requests.py`)
- Pattern: `AddSourceRequest.model_validate(request.get_json())`

### Error Handling
- Custom errors via `SourceNotFoundError` and similar
- Standardized 400/404/500 response patterns

### Performance Characteristics
- Current endpoints designed for bibliographic metadata (small payloads)
- Text upload requires handling up to 100KB+ content

## Missing Components for Text Upload

### Backend Gaps
1. **Text Storage Service**: No existing service for storing/retrieving text content
2. **Text-specific Models**: Current `Source` model lacks text fields and metadata
3. **Search Integration**: Text content search needs implementation
4. **Content Type Handling**: No `contentType` field in current model

### Frontend Gaps  
1. **Text Upload UI**: No existing interface for text input
2. **Content Management UI**: Need list/detail views for text content
3. **Preview Components**: Text preview functionality

### Infrastructure Gaps
1. **Content Indexing**: Assistant integration for text content
2. **Search Backend**: Full-text search for uploaded content
3. **Rate Limiting**: May need adjustment for larger text payloads

## Implementation Recommendations

### Option A: Extend Existing Source Model
**Pros**: Reuse existing infrastructure, simpler integration
**Cons**: Mixes bibliographic and text concepts, may need null fields

```python
# Proposed extension
class Source:
    # Existing fields...
    content: str | None = None  # Text content (if text upload)
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    contentType: Literal["documentation", "notes", "code", "other"] = "other"
    # Keep file_ref for backward compatibility
```

### Option B: Separate TextContent Model
**Pros**: Clean separation of concerns, optimized for text
**Cons**: More complex, duplicate some infrastructure

```python
class TextContent:
    id: TextContentId
    source_id: SourceId  # Reference to parent Source (optional)
    userId: str
    title: str
    content: str
    # ... other text-specific fields
```

### Recommended Approach: Hybrid
1. **Extend `Source`** with optional text fields
2. **Add `contentType`** to distinguish text vs. file sources
3. **Reuse existing services** with conditional logic
4. **Create text-specific subroutines** where needed

## Dependencies to Review

### Required Updates
1. **Database Schema**: MongoDB collection updates
2. **Service Layer**: New/updated command handlers
3. **API Layer**: New/updated endpoints for text operations
4. **Frontend**: Complete UI implementation
5. **Search**: Full-text indexing configuration

### Integration Testing
- Test with existing source library functionality
- Verify assistant content ingestion works
- Ensure backward compatibility with file-based sources

## Risk Areas

### Technical Debt
- Mixing text and file concepts in same model
- Performance impact of large text fields in queries
- Search complexity across different content types

### Migration Complexity
- Need to handle existing `Source` records during schema update
- Data migration strategy for adding new fields
- Backward compatibility for existing API consumers

### Security Considerations
- Text content may require different sanitization than file references
- Size limits and validation for user-generated content
- Privacy: text content may contain sensitive information

## Next Steps for Implementation

### Phase 1: Backend Foundation
1. Update `Source` model with text fields
2. Create text-specific request/response models
3. Add text content validation logic
4. Implement text storage service

### Phase 2: API Layer
1. Extend existing endpoints or add new text-specific endpoints
2. Update error handling for text-specific cases
3. Add rate limiting for text uploads

### Phase 3: Frontend
1. Create text upload component
2. Build content management interface
3. Integrate with existing UI patterns

### Phase 4: Integration
1. Connect to assistant indexing
2. Implement text search
3. Add analytics and monitoring

## Key Decisions Needed
1. **Storage Strategy**: Embed text vs. reference vs. separate collection
2. **API Design**: Extend existing endpoints vs. new `/text` sub-resource
3. **Content Limits**: Final character limits and validation rules
4. **Versioning Approach**: Simple version number vs. full history
5. **Search Implementation**: MongoDB text search vs. dedicated search engine

## References
- [Text Upload Intake Document](./text-upload-intake.md)
- [Feature Specification](./source_library_text_upload.feature)
- [Project README](../../README.md)
- [Source Library API](../../backend/domain/src_lib/api/routes.py)
- [Source Model](../../backend/domain/src_lib/models/aggregates.py)