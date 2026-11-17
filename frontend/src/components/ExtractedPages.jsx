export default function ExtractedPages({ pages }) {
  return (
    <div className="extracted-section">
      <div className="card-header section-subhead">
        <div>
          <span className="card-step">RECORD ARCHIVE</span>
          <h2 className="card-title">Extracted Document Text</h2>
        </div>
        <span className="status-label">Sequential Page View</span>
      </div>

      <div className="pages-stream">
        {pages.map((page) => (
          <article className="page-folio" key={page.page_number}>
            <div className="folio-header">
              <span className="folio-number">PAGE {String(page.page_number).padStart(2, "0")}</span>
              <span className="folio-meta">
                {page.text ? `${page.text.length} characters` : "No text content"}
              </span>
            </div>
            <div className="folio-body">
              {page.text ? (
                <p className="folio-text">{page.text}</p>
              ) : (
                <p className="folio-empty">
                  No selectable text found on this page. Optical character recognition (OCR) will be
                  applied in subsequent milestones.
                </p>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
