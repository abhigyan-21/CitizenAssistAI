function DimensionCard({ number, title, status, statusType, detail }) {
  return (
    <article className="dimension-card">
      <div className="dimension-header">
        <span className="dimension-number">{number}</span>
        <span className={`status-pill ${statusType === "active" ? "status-active" : "status-planned"}`}>
          {status}
        </span>
      </div>
      <h3 className="dimension-title">{title}</h3>
      <p className="dimension-detail">{detail}</p>
    </article>
  );
}

export default function PipelineSection() {
  return (
    <section className="civic-card pipeline-card">
      <div className="card-header">
        <div>
          <span className="card-step">EVALUATION FRAMEWORK</span>
          <h2 className="card-title">CDTM Trustworthiness Evaluation</h2>
        </div>
        <span className="status-label">Five Trustworthiness Dimensions</span>
      </div>

      <p className="pipeline-lead">
        The Citizen Document Trustworthiness Model (CDTM) evaluates automated assistance systems
        against five critical dimensions to prevent bureaucratic hallucinations and procedural errors.
      </p>

      <div className="cdtm-grid">
        <DimensionCard
          number="01"
          title="Source Fidelity"
          status="Grounded QA Active"
          statusType="active"
          detail="Verifies that all extracted statements and retrieved passages correspond strictly to verified clauses in the official source document without extrapolation."
        />
        <DimensionCard
          number="02"
          title="Semantic Fidelity"
          status="Phase 04 — Active"
          statusType="active"
          detail="Plain-language simplification with two-call AI fidelity review. Reviewer independently checks whether simplified text preserves all conditions, exclusions and financial amounts."
        />
        <DimensionCard
          number="03"
          title="Plain-Language Clarity"
          status="Planned Milestone"
          statusType="planned"
          detail="Measures readability and structural simplification, transforming convoluted administrative terminology into plain, comprehensible English for citizen audiences."
        />
        <DimensionCard
          number="04"
          title="Cross-Lingual Preservation"
          status="Planned Milestone"
          statusType="planned"
          detail="Evaluates semantic and numeric consistency in Hindi translations, verifying that statutory dates, monetary benefits, and official terms remain intact."
        />
        <DimensionCard
          number="05"
          title="Procedural Actionability"
          status="Planned Milestone"
          statusType="planned"
          detail="Audits institutional action pathways (application portals, verification authorities, nodal officers) to prevent misdirection of citizen applicants."
        />
      </div>
    </section>
  );
}
