# Technical Stack & Architecture Reference

**CitizenAssist AI** is an academic and civic research demonstrator implementing the **Citizen Document Trustworthiness Model (CDTM)**. It is built to evaluate and improve how artificial intelligence transforms, simplifies, translates, and explains complex Indian administrative and statutory documents for citizens.

This document provides a comprehensive breakdown of the entire technology stack, including all languages, frameworks, libraries, APIs, algorithms, and a phase-by-phase architectural mapping explaining **what technology is used, why it was chosen, and which phase leverages it**.

---

## 1. High-Level Technology Inventory

### 1.1 Frontend Technologies
| Technology | Version / Spec | Category | Why It Was Chosen |
|---|---|---|---|
| **React** | `19.x` | UI Framework | Declarative, component-driven UI architecture. Handles complex multi-state workflows across 7 guided demonstration phases with granular, reactive UI updates. |
| **Vite** | `8.x` | Build Tool & Dev Server | Ultra-fast native ES-module development server with instant Hot Module Replacement (HMR) and optimized rollup production bundles (~380ms build time). |
| **Lucide React** | Latest | Iconography | Modern, clean, tree-shakeable SVG icons tailored for civic and editorial user interfaces, status indicators, and diagnostic dashboards. |
| **Civic Editorial CSS** | Native CSS3 | Design System | High-contrast, publication-grade civic editorial design system. Built with native CSS custom properties (variables) for theme consistency, zero layout shift, and zero external CSS framework overhead (no Tailwind/Bootstrap bloat). |

### 1.2 Backend Technologies
| Technology | Version / Spec | Category | Why It Was Chosen |
|---|---|---|---|
| **Python** | `3.11+` | Runtime Language | Robust typing, native `asyncio` event loop for non-blocking I/O, and an extensive standard library for deterministic processing. |
| **FastAPI** | `>=0.115` | Web Framework | High-performance asynchronous ASGI web framework. Automatically generates interactive OpenAPI/Swagger documentation (`/docs`) and seamlessly integrates with Pydantic for request/response validation. |
| **Uvicorn** | `>=0.30` | ASGI Web Server | Lightning-fast asynchronous server implementation for Python, running on `uvloop` and `httptools` for concurrent request handling. |
| **Pydantic v2 & Pydantic-Settings** | `>=2.4` | Validation & Settings | Strict runtime schema validation, data serialization, and environment variable configuration from `.env` files with type safety. |
| **PyMuPDF (`fitz`)** | `>=1.24` | PDF Extraction | Fast, low-latency C-based PDF text parser. Extracts text page-by-page, retains spatial reading order, and detects image-only/scanned pages lacking selectable text. |
| **python-multipart** | `>=0.0.9` | Request Parsing | Enables high-throughput, streaming multipart form-data parsing for PDF document uploads. |

### 1.3 AI Providers & Inference Models
| Provider / API | Model ID | Primary Role | Why It Was Chosen |
|---|---|---|---|
| **Groq Cloud API (`groq` SDK)** | `openai/gpt-oss-20b` | Primary Generation & Audit Model | Hardware-accelerated LPUs deliver ultra-low inference latency (~300–500 tokens/sec), structured JSON mode enforcement, and high instruction compliance for statutory groundings. |
| **Groq Cloud API (`groq` SDK)** | `qwen/qwen3.8-27b` | Automated Fallback Model | Configured as an automatic failover model when the primary model encounters rate limits (HTTP 429) or transient provider capacity exhaustion. |
| **Google Gemini API (`google-genai` SDK)** | `gemini-1.5-flash` | Alternative Pluggable Provider | Secondary provider option for multi-provider resilience and comparative evaluation across distinct model families. |

### 1.4 Algorithmic & Deterministic Libraries
| Library / Algorithm | Location | Purpose & Justification |
|---|---|---|
| **Pure-Python Okapi BM25** | `app/retrieval/bm25.py` | Built from scratch using Python standard library (`math`, `re`). Provides transparent, fully deterministic lexical ranking without bulky NLP dependencies (no PyTorch, Transformers, or NLTK). |
| **Devanagari & Entity Normalizer** | `app/services/translation_service.py` | Custom regex and Unicode normalizer. Audits preservation of Hindu-Arabic numerals, Devanagari numerals (`०-९`), currency symbols (`₹`, `Rs`), and statutory dates. Numbers cannot be left to probabilistic LLMs alone. |
| **SequenceMatcher (`difflib`)** | Python Standard Library | Computes deterministic similarity ratios between original statutory passages and plain-language rewrites to verify transformation quality. |
| **Flesch Readability Formulas** | `app/evaluation/accessibility.py` | Computes structural readability proxies (Flesch Reading Ease, Flesch-Kincaid Grade Level, sentence length, and bureaucratic acronym detection like DBT, UT, KCC). |

---

## 2. Phase-by-Phase Technical Mapping

CitizenAssist AI organizes its research demonstration into **7 sequential guided walkthrough phases**. Below is the exact technology stack utilized in each phase and the architectural rationale behind it:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      7-PHASE GUIDED DEMONSTRATION                      │
│                                                                        │
│   Phase 1: Foundation (PDF Upload & Extraction)                        │
│      └─► PyMuPDF · python-multipart · SHA-256 · In-Memory Store        │
│                                                                        │
│   Phase 2: Retrieval (BM25 Lexical Search)                             │
│      └─► Pure-Python Okapi BM25 · Math IDF · Term Tokenizer            │
│                                                                        │
│   Phase 3: Grounded Q&A (AI-Assisted Inquiry)                          │
│      └─► Groq (gpt-oss-20b) · Fallback (qwen3.8-27b) · Citation Check  │
│                                                                        │
│   Phase 4: Semantic Fidelity (Plain Language)                          │
│      └─► Two-Call AI Pipeline · difflib · Sukanya Presentation Data    │
│                                                                        │
│   Phase 5: Cross-Lingual Fidelity (Hindi Translation)                  │
│      └─► Deterministic Numeral Normalizer · AI Review Pass · सरल हिंदी │
│                                                                        │
│   Phase 6: CDTM Multidimensional Evaluation Dashboard                  │
│      └─► 5 Independent Evaluators · Failure Bench · JSON Inspector     │
│                                                                        │
│   Phase 7: Comparative Demonstration Showcase                          │
│      └─► Dual-Paradigm Pipeline (Naive RAG vs. CDTM Verified RAG)      │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Foundation (PDF Upload & Extraction)
- **Primary Goal:** Ingest authentic government PDFs, extract selectable text page-by-page, chunk document boundaries, and detect non-selectable/scanned pages.
- **Technologies Used:**
  - **PyMuPDF (`fitz`):** Extracts clean text page-by-page while preserving structural flow and detecting pages with zero selectable text.
  - **`python-multipart`:** Handles file upload streaming via FastAPI `UploadFile`.
  - **Python `hashlib`:** Computes a SHA-256 cryptographic digest of the raw PDF bytes, generating a deterministic, collision-resistant `document_id`.
  - **Page-Aware Sliding Chunker (`app/document/chunker.py`):** Slices text into overlapping passages tagged with deterministic IDs (`{doc_id}-p{page}-c{idx}`) and explicit page numbers.
  - **Thread-Safe In-Memory Store (`app/document/store.py`):** Uses Python `threading.Lock` to manage active documents without requiring external database setup.
  - **Frontend:** React HTML5 Drag & Drop File API, Lucide document indicators.
- **Why This Tech:** Standard OCR is non-deterministic and heavy; PyMuPDF is instantaneous (< 50ms) and provides exact page boundary metadata necessary for legal citation.

---

### Phase 2: Retrieval (BM25 Lexical Search)
- **Primary Goal:** Index extracted passages and allow citizens to search statutory rules using keyword relevance scoring.
- **Technologies Used:**
  - **Pure-Python Okapi BM25 (`app/retrieval/bm25.py`):** Custom implementation of the Okapi BM25 retrieval function using Python's standard `math` and `re` modules.
  - **Term Frequency & IDF Calculation:** Calculates inverse document frequency across chunks with standard parameters ($k_1 = 1.5$, $b = 0.75$).
  - **Frontend:** Controlled search input with real-time score ranking, highlighted term matching, and raw score badges.
- **Why This Tech:** Administrative documents rely on exact statutory phrasing (e.g., *"G.S.R. 914(E)"*, *"Section 4(1)"*). Dense vector embeddings often hallucinate semantic proximity or fail on alphanumeric clause references. BM25 provides explainable, reproducible, and verifiable ranking.

---

### Phase 3: Grounded Q&A (Evidence-Grounded Inquiry)
- **Primary Goal:** Answer citizen questions strictly using retrieved document passages, citing exact source pages and abstaining when evidence is absent.
- **Technologies Used:**
  - **Groq API (`openai/gpt-oss-20b`):** Fast inference generating answers constrained to retrieved chunks.
  - **Groq Fallback (`qwen/qwen3.8-27b`):** Automatically called if rate limits or 429 status codes occur.
  - **Google Gemini API (`gemini-1.5-flash`):** Alternate provider selectable via `AI_PROVIDER=gemini`.
  - **Server-Side Citation Validator (`app/services/qa_service.py`):** Server-side verification ensuring every chunk ID cited in the answer exists in the active document store. Rejects fabricated citations.
  - **Insufficient Evidence Detector:** Detects missing facts and triggers explicit abstention rather than hallucinating answers.
  - **Frontend:** Interactive citation badges (`[Page N]`) with smooth auto-scroll to evidentiary passages.
- **Why This Tech:** Citizen trust requires strict provenance. Generative models without server-side validation fabricate chunk references. Decoupling the provider behind an abstract `AIProvider` interface allows swapping models seamlessly.

---

### Phase 4: Semantic Fidelity (Plain-Language Simplification)
- **Primary Goal:** Transform dense administrative jargon into simple, citizen-friendly language while guaranteeing no statutory rules, exclusions, or deadlines are lost.
- **Technologies Used:**
  - **Two-Call AI Pipeline (`app/services/simplification_service.py`):**
    - *Call 1 (Generation):* Rewrites administrative text to plain English.
    - *Call 2 (Independent Audit):* Evaluates whether eligibility rules, monetary limits, or exclusions were dropped or distorted.
  - **Python `difflib.SequenceMatcher`:** Deterministically computes the lexical modification ratio to verify that actual simplification occurred.
  - **Sukanya Presentation Fixtures (`app/demo/sukanya_fixtures.py`):** Verified 11-clause reference fixtures for the Sukanya Samriddhi Scheme ensuring offline-compatible presentations.
  - **Frontend:** Side-by-side split workbench comparing original legal text with plain English simplification and preserved condition badges.
- **Why This Tech:** Standard LLMs often drop negative conditions (e.g. omitting *"not eligible if income tax payer"*) when trying to simplify. The independent Call 2 review audits the output specifically for condition retention.

---

### Phase 5: Cross-Lingual Fidelity (Hindi Translation & Term Audit)
- **Primary Goal:** Translate administrative rules to Hindi Devanagari while strictly maintaining monetary amounts, statutory dates, and exclusion rules.
- **Technologies Used:**
  - **Two-Tier Verification Protocol (`app/services/translation_service.py`):**
    - *Tier 1 (Deterministic Extraction):* Normalizes Hindu-Arabic numerals, Devanagari numerals (`०-९`), and currency amounts (`₹250`, `₹1,50,000`) using regex. Verifies exact mathematical equality between source and target.
    - *Tier 2 (AI Semantic Reviewer):* Second-pass AI review auditing whether legal conditions or exclusions drifted during translation.
  - **Plain-Language Hindi Engine (*सरल हिंदी*):** Secondary transformation converting formal administrative Hindi into everyday spoken Hindi.
  - **Frontend:** `BilingualPanel.jsx` with tabs for Formal Translation vs. *सरल हिंदी* and entity verification checklists.
- **Why This Tech:** Probabilistic language models frequently mistranslate numbers or confuse Indian numbering systems (e.g. converting lakhs to millions incorrectly). Deterministic regex guarantees numbers match 100%.

---

### Phase 6: CDTM Multidimensional Evaluation Dashboard
- **Primary Goal:** Evaluate the document transformation across all five CDTM dimensions, allow failure testing, and inspect diagnostic payloads.
- **Technologies Used:**
  - **CDTM Evaluation Engine (`app/evaluation/engine.py`):** Integrates independent evaluators for:
    1. *Source Fidelity* (extraction validity, empty page detection).
    2. *Semantic Fidelity* (condition and rule preservation count).
    3. *Evidence Grounding* (atomic claim-level passage corroboration).
    4. *Cross-Lingual Fidelity* (term and numeral consistency).
    5. *Citizen Accessibility* (structural readability formulas).
  - **Controlled Failure Injection Bench (`app/evaluation/demo_failures.py`):** Dedicated endpoints (`/api/demo/evaluate-failure`) simulating intentional flaws (e.g. missing text, hallucinated money, inverted rules) to prove evaluators catch errors.
  - **Readability Formulas:** Standard Flesch Reading Ease and Flesch-Kincaid Grade Level formulas computed natively.
  - **Frontend:** Interactive scorecards, expandable evidence drawers, failure demonstration buttons, and raw JSON schema inspector.
- **Why This Tech:** **Core Invariant:** CDTM strictly forbids creating a composite or single weighted trust score. Each dimension must be evaluated independently so failures in one area cannot be hidden by high marks in another.

---

### Phase 7: Comparative Demonstration Showcase (Dual-Paradigm)
- **Primary Goal:** Side-by-side comparison illustrating why CDTM governance is necessary compared to naive, ungrounded generative AI.
- **Technologies Used:**
  - **Dual-Prompt Execution Architecture (`app/api/routes.py`):**
    - *Basic/Naive RAG:* Standard system prompt without citation validation or strict grounding.
    - *CDTM-Guided RAG:* Strict prompt grounding, server-side citation enforcement, and claim-level verification.
  - **Frontend:** `ComparativeShowcaseView.jsx` displaying side-by-side responses with red/green discrepancy indicators highlighting hallucinations and unsupported claims.
- **Why This Tech:** Demonstrates real-world utility by showing evaluators exactly what goes wrong when using off-the-shelf LLMs for citizen services versus when applying CDTM verification.

---

## 3. Storage, Testing & Deployment Architecture

### 3.1 Data Architecture
- **In-Memory Thread-Safe Store:** To ensure zero database configuration for researchers and evaluators, all documents, chunks, and evaluations are managed in memory guarded by `threading.Lock`.
- **Pre-Verified Sukanya Samriddhi Fixtures:** Hardcoded statutory reference fixtures from the Gazette of India G.S.R. 914(E) enabling 100% offline demonstration capability.

### 3.2 Testing & Quality Assurance
- **Framework:** Python Standard Library `unittest` & `unittest.mock`.
- **Suite Size:** **114 automated backend unit tests** covering:
  - Document chunking and boundary integrity.
  - Pure-Python BM25 ranking and scoring.
  - Groq and Gemini API adapters, retries, and timeouts.
  - Server-side citation rejection and abstention logic.
  - Deterministic entity extraction and Devanagari normalization.
  - CDTM evaluation engine and failure demonstration endpoints.
- **Frontend Verification:** Type checks and asset bundling via `vite build` (0 bundle errors).

### 3.3 Security & Privacy Design
- **Zero API Key Leakage:** Keys (`GROQ_API_KEY`, `GEMINI_API_KEY`) reside exclusively in backend environment memory and are never transmitted to client browsers.
- **Public Domain Safety:** Designed strictly for publicly accessible administrative gazettes and citizen schemes; does not store or process citizen PII (Personally Identifiable Information).
