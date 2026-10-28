from dataclasses import dataclass

from markdownify import markdownify as md

@dataclass(frozen=true)
class Chunk:
    text: str                                           # The chunk text
    start_index: int                                    # Starting position in original text
    end_index: int                                      # Ending position in original text
    token_count: int                                    # Number of tokens in chunk
    context: Optional[str] = None                       # Optional overlap context text
    embedding: Union[list[float], "np.ndarray", None] = None  # Optional embedding vector

@dataclass(frozen=true)
class ChunkedManuscript:
    id: UUID
    project_id: UUID
    title: str
    chunks: dict[UUID, list[Chunk]]

class ChunkManuscriptService:

    def __init__(chunker: Chunker) -> None:
        self._chunker = chunker

    def execute(self, manuscript: Manuscript) -> ChunkedManuscript:
        chunks: dict[UUID, list[Chunk]] = {}

        # Loop through manuscript sections dictionary
        # for every section body:
        #   convert to markdown
        #   chunk section into list of chunks
        #   add section id and chunked section body to chunks dictionary
        for id, section in manuscript.sections:
            markdown_section_body: str = md(section.body, heading_style="ATX")
            chunked_section_body: list[Chunk] = self.chunker(markdown_section)
            chunks.update({id, chunked_section_body})
        
        # build the chunked manuscript
        chunked_manuscript = ChunkedManuscript(
            id=manuscript.id, 
            project_id=manuscript.project_id, 
            title=manuscript.title, 
            chunks=chunks
        )

        return chunked_manuscript