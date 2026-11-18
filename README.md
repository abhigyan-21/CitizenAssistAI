# CitizenAssist AI

A research prototype that helps citizens understand Indian administrative and government documents using evidence-grounded AI question answering, plain-language simplification, and cross-lingual translation guided by the Citizen Document Trustworthiness Model (CDTM).

> **Research context:** Software demonstrator for the Citizen Document Trustworthiness Model (CDTM) — a 5-dimensional framework for evaluating how faithfully AI systems transform and explain administrative documents across Source Fidelity, Semantic Fidelity, Evidence Grounding, Cross-Lingual Fidelity, and Accessibility.  
> *This is an academic and civic research prototype, not a production government portal.*

---

## Architecture & Implementation Status

| Phase | Module / Capability | Implementation Details | Status |
|---|---|---|---|
| **Phase 1** | **Document Docket & Extraction** | PyMuPDF page-by-page extraction, deterministic page-aware sliding window chunking, SHA-256 fingerprinting, thread-safe in-memory store. | ✅ Complete |
| **Phase 2** | **Deterministic BM25 Retrieval** | Pure-Python BM25 indexer (Okapi BM25, no external NLP dependencies), term frequency tokenization, raw score ranking. | ✅ Complete |
| **Phase 3** | **Evidence-Grounded Q&A** | Multi-provider architecture (Groq primary, Gemini alternate), strict prompt grounding, server-side citation validation, ungrounded claim abstention. | ✅ Complete |
| **Phase 4** | **Semantic Fidelity & Simplification** | Two-call architecture: Call 1 plain-language simplification; Call 2 independent reviewer for condition & statutory rule preservation. | ✅ Complete |
| **Phase 5** | **Cross-Lingual Fidelity (Hindi)** | English-to-Hindi Devanagari translation, deterministic numeral/date/term preservation, secondary semantic audit, and plain *सरल हिंदी* simplification. | ✅ Complete |
| **Phase 6** | **CDTM Evaluation Engine** | Evaluators across all 5 CDTM dimensions: Source Fidelity, Semantic Fidelity, Evidence Grounding, Cross-Lingual Fidelity, Accessibility. | ✅ Complete |
| **Phase 7** | **Interactive CDTM Dashboard** | Per-dimension status metrics (Verified, Potential Issue, Requires Human Review), controlled failure demonstrations, audit trail. | ✅ Complete |
| **Phase 8** | **Comparative Demonstration Showcase** | Side-by-side comparison of Naive/Basic RAG vs. CDTM-Guided Governance, highlighting hallucination interception and citation grounding. | ✅ Complete |
| **Phase 9** | **Empirical Validation & User Study** | Structured empirical user evaluation on authentic public schemes (PM-KISAN, Sukanya Samriddhi). | ⬜ Planned |

**Automated Tests:** **114 backend unit tests**, 100% passing.  
**Frontend Interface:** Modern 8-Phase Guided Walkthrough UI with step-by-step navigation, interactive workbenches, and Civic Editorial design system.

---

## Section-Accurate Demo Mode (Sukanya Samriddhi)

CitizenAssist AI includes an offline-capable, section-matched presentation mode for the **Sukanya Samriddhi Account Scheme (2019 / G.S.R. 914(E))**:
- **Masthead Toggle:** Click the **Book Open icon (`📖`)** in the top navigation bar to toggle Demo Mode on or off. A clean in-app status banner indicates when demo fixtures are active.
- **Section-Aware Alignment:** The system matches input text against 11 scheme clauses (Opening of Account, Deposits, Interest, Premature Closure, Withdrawal, Maturity, etc.) ensuring that selected document chunks strictly output their corresponding plain-language English, formal Hindi translation, and citizen-friendly *सरल हिंदी* without cross-paragraph displacement.

---

## Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** 3.11+
- **Node.js:** 18+
- **Groq API Key:** (Free tier at https://console.groq.com)
  - Primary Model: `openai/gpt-oss-20b`
  - Automatic Fallback Model: `qwen/qwen3.8-27b`
- **Gemini API Key:** *(Optional, from https://aistudio.google.com)*

---

## Quickstart Setup

### 1. Backend Setup

```powershell
cd CitizenAssistAI\backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env
# Edit .env and supply your GROQ_API_KEY
notepad .env

# Run FastAPI server
uvicorn app.main:app --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger API Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```powershell
cd CitizenAssistAI\frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

- Client Application: `http://localhost:5173`

---

## Running Unit Tests

All 113 backend tests can be run via Python's standard `unittest` suite:

```powershell
# From the CitizenAssistAI\backend directory:
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Expected result:
```text
Ran 113 tests in ~8.5s
OK
```

Frontend production build verification:
```powershell
cd CitizenAssistAI\frontend
npm run build
```

---

## Environment Variables

Configure `backend/.env` (reference `backend/.env.example`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `AI_PROVIDER` | No | `groq` | Selected provider (`groq` or `gemini`) |
| `GROQ_API_KEY` | Yes (for Groq) | — | Groq Cloud API access key |
| `GROQ_MODEL` | No | `openai/gpt-oss-20b` | Primary Groq model |
| `GROQ_FALLBACK_MODEL` | No | `qwen/qwen3.8-27b` | Automatic fallback model on 429 / capacity exhaustion |
| `GEMINI_API_KEY` | Yes (if Gemini) | — | Google AI Studio API key |
| `GEMINI_MODEL` | No | `gemini-1.5-flash` | Gemini model name |
| `MAX_UPLOAD_MB` | No | `20` | Max document upload threshold in MB |

---

## Guided Walkthrough Phases

1. **Phase 1 (Upload & Extraction):** Upload authentic administrative PDF; inspect page-by-page text chunks, document fingerprint, and extraction warnings.
2. **Phase 2 (BM25 Keyword Search):** Query statutory passages using deterministic BM25 ranking.
3. **Phase 3 (Grounded Q&A):** Ask citizen questions; observe server-side citation validation, clickable evidence badges, and explicit abstentions for ungrounded claims.
4. **Phase 4 (Semantic Fidelity):** Plain-language simplification alongside independent Call 2 condition preservation verification.
5. **Phase 5 (Cross-Lingual Fidelity):** Devanagari translation with deterministic number/date preservation, plus plain *सरल हिंदी* simplification.
6. **Phase 6 (CDTM Evaluation Engine):** Run multi-dimensional evaluators against document transformations.
7. **Phase 7 (CDTM Dashboard):** Comprehensive overview of Trustworthiness Dimensions, including controlled failure demonstration audits.
8. **Phase 8 (Comparative Showcase):** Direct comparison showing how standard naive LLM/RAG hallucinates or drops statutory conditions compared to CDTM-guided governance.

---

## Safety & Governance Principles

- **Zero Fabricated Citations:** AI answers must explicitly cite document chunks; fabricated chunk citations are rejected server-side.
- **Strict Provenance:** Transformations (simplifications and translations) maintain explicit provenance linking back to specific page chunks.
- **Decoupled Verification:** Generative output generation is strictly decoupled from evaluation/reviewer calls.
- **Local Key Privacy:** API keys reside exclusively on the backend server and are never exposed to browser clients.
