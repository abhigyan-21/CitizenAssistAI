export default function CitationBadge({ citation, isActive, onClick }) {
  return (
    <button
      type="button"
      className={`citation-pill${isActive ? " citation-pill-active" : ""}`}
      onClick={() => onClick(citation.chunk_id)}
      title={`Click to inspect passage on Page ${citation.page_number} (Chunk: ${citation.chunk_id})`}
    >
      [Page {citation.page_number}]
    </button>
  );
}
