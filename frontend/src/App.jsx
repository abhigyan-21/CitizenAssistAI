import { useState } from "react";
import { FileUp, FileText, ShieldCheck, Languages, Search, AlertCircle, CheckCircle2 } from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function extract(event) {
    event.preventDefault();
    if (!file) return setError("Choose a PDF first.");
    setBusy(true); setError(""); setResult(null);
    const body = new FormData(); body.append("file", file);
    try {
      const response = await fetch(`${API}/api/documents/extract`, { method: "POST", body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Extraction failed.");
      setResult(data);
    } catch (err) { setError(err.message || "Could not connect to the backend."); }
    finally { setBusy(false); }
  }

  return <main className="shell">
    <header className="topbar"><a className="brand" href="#"><span className="brandmark"><ShieldCheck size={20}/></span>CitizenAssist <b>AI</b></a><span className="muted">Research demonstrator · CDTM-guided</span></header>
    <section className="hero"><div className="eyebrow">ADMINISTRATIVE DOCUMENT UNDERSTANDING</div><h1>Government information,<br/><span>made easier to understand.</span></h1><p>Upload an administrative document to begin. This first milestone extracts page-level text; simplification, Hindi translation, evidence-grounded answers and CDTM evaluation will follow.</p></section>
    <section className="panel">
      <div className="sectionhead"><div><div className="eyebrow">STEP 01</div><h2>Upload a document</h2></div><span className="pill">PDF extraction</span></div>
      <form onSubmit={extract}>
        <label className="dropzone"><input type="file" accept="application/pdf,.pdf" onChange={e=>{setFile(e.target.files?.[0]||null);setResult(null);setError("");}}/><span className="uploadicon"><FileUp size={25}/></span><strong>{file ? file.name : "Choose a PDF document"}</strong><span className="muted">{file ? `${(file.size/1048576).toFixed(2)} MB` : "PDF format · Maximum 20 MB"}</span><span className="link">Browse files</span></label>
        {error && <div className="alert error"><AlertCircle size={17}/>{error}</div>}
        <button className="primary" disabled={!file||busy}>{busy ? "Extracting…" : "Extract document text"}</button>
      </form>
    </section>
    {result && <section className="panel result">
      <div className="resulthead"><div className="filetitle"><span className="fileicon"><FileText/></span><div><b>{result.filename}</b><div className="muted">{result.page_count} page(s) processed</div></div></div><span className="success"><CheckCircle2 size={15}/> Extraction complete</span></div>
      {result.warnings.length>0 && <div className="alert warning"><AlertCircle size={17}/><div>{result.warnings.map(w=><p key={w}>{w}</p>)}</div></div>}
      <div className="sectionhead extracted"><h2>Extracted text</h2><span className="muted">Page-level output</span></div>
      {result.pages.map(page=><article className="page" key={page.page_number}><div className="eyebrow">PAGE {page.page_number}</div><p>{page.text || "No selectable text found. OCR will be added in a later milestone."}</p></article>)}
    </section>}
    <section className="next"><div className="eyebrow">COMING NEXT</div><h2>Citizen assistance pipeline</h2><div className="features">
      <Feature icon={<FileText/>} title="Simplification" detail="Convert administrative language into plain English."/>
      <Feature icon={<Languages/>} title="Hindi translation" detail="Preserve important facts across languages."/>
      <Feature icon={<Search/>} title="Evidence-grounded Q&A" detail="Answer with source passages and page references."/>
      <Feature icon={<ShieldCheck/>} title="CDTM evaluation" detail="Inspect five dimensions and potential issues."/>
    </div></section>
    <footer><span>CitizenAssist AI · Proof of concept</span><span>Verify outputs against the original government source.</span></footer>
  </main>;
}
function Feature({icon,title,detail}) { return <article className="feature"><span className="featureicon">{icon}</span><h3>{title}</h3><p>{detail}</p><span className="pill">Planned</span></article>; }
