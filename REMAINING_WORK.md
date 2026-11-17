# CitizenAssist AI — Remaining Work & Development Roadmap

> **Last updated:** 2026-11-18  
> **For:** Next developer continuing CitizenAssist AI  
> **Cross-reference:** See `PROJECT_HANDOVER.md` for architecture, API documentation and setup instructions  
> **Repository:** https://github.com/abhigyan-21/CitizenAssistAI *(private)*

---

## Quick Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — Foundation | ✅ Complete | PDF extraction, chunking, storage |
| Phase 2 — Retrieval | ✅ Complete | BM25, search API, frontend search |
| Phase 3 — AI-Assisted Q&A | ✅ Complete (locally) | Gemini + Groq implemented; Groq not yet pushed |
| Phase 4 — Semantic Fidelity | ✅ Complete | Plain-language simplification & condition review |
| Phase 5 — Cross-Lingual Fidelity | ✅ Complete | Hindi translation & deterministic term preservation |
| Phase 6 — CDTM Evaluation Engine | ✅ Complete | Independent evaluation across all five dimensions |
| Phase 7 — CDTM Dashboard | ✅ Complete | Frontend evaluation display & research demo controls |
| Phase 8 — Complete Demonstration | ✅ Complete | Comparative demo (Basic vs CDTM) & pipeline tracker |
| Phase 9 — Validation and Study | ⬜ Not started | Empirical evaluation |

---

## Completion Checklist

Use this to track progress. Tick items as they are completed.

### Phase 1 — Foundation
- [x] PDF upload and validation
- [x] PyMuPDF page-by-page text extraction
- [x] Warning system for pages without selectable text
- [x] Overlapping, page-bounded text chunking
- [x] SHA-256 document ID generation
- [x] Chunk ID scheme (`docid-p0001-c001`)
- [x] In-memory document store with thread safety
- [x] Automated tests for extraction and store

### Phase 2 — Retrieval
- [x] Pure-Python BM25Okapi implementation
- [x] Tokeniser preserving hyphenated terms
- [x] BM25Retriever wrapping per-document chunks
- [x] BM25 search API endpoint
- [x] Alternative search endpoint (body-based document_id)
- [x] Frontend BM25 search interface with scored results
- [x] Automated BM25 tests (tokeniser, scoring, retriever)

### Phase 3 — AI-Assisted Q&A
- [x] Abstract AIProvider interface
- [x] GroundedAnswerResponse schema
- [x] MockAIProvider for tests
- [x] GeminiProvider (google-genai SDK, structured output)
- [x] GroqProvider (AsyncGroq, JSON object mode) *(local only — not yet pushed)*
- [x] Provider selection via AI_PROVIDER env var *(local only)*
- [x] QAService: BM25 retrieval → provider → citation validation
- [x] Backend citation validation (fabricated ID rejection)
- [x] Insufficient-evidence abstention (zero passages + zero valid citations)
- [x] Ask endpoint (`POST /api/documents/{id}/ask`)
- [x] Frontend Q&A panel with citation badges and evidence drawer
- [x] 47 automated tests all passing *(local only)*
- [ ] **Push Groq integration to GitHub** — blocked on original developer
- [ ] Real Groq API integration test with an actual PDF
- [ ] Real Gemini API integration test with an actual PDF

### Phase 4 — Semantic Fidelity
- [ ] Plain-language simplification endpoint
- [ ] Eligibility rule and condition preservation checking
- [ ] Omission and contradiction detection
- [ ] Comparison view: original passage vs simplified explanation
- [ ] Semantic Fidelity evaluation module
- [ ] Automated tests

### Phase 5 — Cross-Lingual Fidelity
- [ ] English-to-Hindi translation endpoint
- [ ] Administrative terminology preservation
- [ ] Preservation of amounts, dates, eligibility, deadlines
- [ ] Bilingual side-by-side comparison view
- [ ] Cross-Lingual Fidelity evaluation module
- [ ] Automated tests

### Phase 6 — CDTM Evaluation Engine
- [ ] Source Fidelity evaluator
- [ ] Semantic Fidelity evaluator
- [ ] Evidence Grounding evaluator
- [ ] Cross-Lingual Fidelity evaluator
- [ ] Citizen Accessibility evaluator
- [ ] Controlled failure demonstrations (all five)
- [ ] Automated tests for each evaluator

### Phase 7 — CDTM Dashboard
- [ ] Per-dimension result cards
- [ ] Supporting evidence panels
- [ ] Detected issue reporting
- [ ] Human review flags
- [ ] Status labels (Verified / Potential Issue / Requires Human Review / Not Evaluated)

### Phase 8 — Complete Demonstration
- [x] Basic vs CDTM-Guided comparison view
- [x] Pipeline phase indicators
- [x] Controlled failure demonstration toggles
- [x] Honest implemented-vs-planned labelling

### Phase 9 — Validation and Study
- [ ] Document corpus selection (English, Hindi, one regional language)
- [ ] Expert evaluation protocol
- [ ] Citizen comprehension evaluation (if feasible)
- [ ] Results recorded and reported accurately

---

## Phase 3 — AI-Assisted Question Answering (Remaining Tasks Only)

> Phases 1 and 2 are complete. Phase 3 core implementation is complete locally. Remaining tasks are integration and push.

### Task 3.R1 — Push Groq Integration to GitHub

**Objective:** Make the Groq provider available to the new developer via the remote repository.

**Why needed:** The Groq implementation exists only in the local working copy. The new developer cannot access it until it is pushed.

**Relevant existing files:**
- `app/ai/groq.py`
- `app/core/config.py`
- `app/services/qa_service.py`
- `app/api/routes.py`
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/tests/test_groq.py`
- `backend/tests/test_qa.py`

**Steps for the original developer:**
```powershell
cd CitizenAssistAI
git checkout -b feature/groq-integration
git add app/ai/groq.py app/ai/__init__.py app/core/config.py
git add app/services/qa_service.py app/api/routes.py
git add requirements.txt .env.example
git add tests/test_groq.py tests/test_qa.py
git add ../PROJECT_HANDOVER.md ../REMAINING_WORK.md
git commit -m "Add Groq AI provider integration (Milestone 6)"
git push origin feature/groq-integration
# Then open a PR to merge into main
```

**Acceptance criteria:** `git clone` on the new developer's machine shows `app/ai/groq.py` and 47 passing tests.

---

### Task 3.R2 — Real Groq API Integration Test

**Objective:** Confirm the Groq integration works end-to-end with a real API key and a real PDF.

**Why needed:** All automated tests use mocked providers. Real API behaviour (model output quality, latency, rate limits) has not been tested.

**Steps:**
1. Add `GROQ_API_KEY=<your_key>` to `backend/.env`
2. Set `AI_PROVIDER=groq` in `backend/.env` (default)
3. Start backend: `uvicorn app.main:app --reload`
4. Start frontend: `npm run dev`
5. Upload a public Indian government PDF (e.g. PM-KISAN operational guidelines)
6. Ask: *"What is the annual financial benefit for an eligible farmer family?"*
7. Verify: answer appears with `[Page N]` badge; badge click scrolls to highlighted passage
8. Ask a question the document does not answer; verify abstention message appears

**Acceptance criteria:** Grounded answer with valid citation, and abstention when evidence is absent. No API key appears in any response.

---

## Phase 4 — Semantic Fidelity

### Task 4.1 — Plain-Language Simplification Endpoint

**Objective:** Given a retrieved passage, generate a simplified plain-English explanation using the AI provider.

**Why needed:** Citizens may not understand formal administrative language even when the correct passage is found. Semantic Fidelity measures whether simplification preserves meaning faithfully.

**Relevant existing files:**
- `app/ai/base.py` — extend AIProvider interface
- `app/services/qa_service.py` — model for a new service
- `app/api/routes.py` — add new endpoint

**Suggested new files (not yet created):**
- `app/services/simplification_service.py` — simplification pipeline
- `app/ai/base.py` — add `simplify_passage()` abstract method (or create separate interface)

**Dependencies:** Phase 3 complete (AI provider architecture in place)

**Implementation approach:**
1. Add `simplify_passage(passage_text, context_question)` to AIProvider interface
2. Implement in GeminiProvider and GroqProvider
3. System prompt must instruct model to preserve all conditions, eligibility rules, amounts and dates
4. Return: `simplified_text`, `source_passage`, `preservation_warnings` (passages where simplification may have dropped conditions)
5. Create `POST /api/documents/{id}/simplify` endpoint accepting `chunk_id`
6. Frontend: show simplified text alongside source passage

**Suggested Git branch:** `feature/semantic-fidelity`

**Acceptance criteria:**
- Simplified text is returned with the source passage for comparison
- Eligibility exclusions present in the source passage are present in the simplified text
- Tests verify both pass-through and known simplification behaviours using MockAIProvider

**Tests required:**
- Unit tests for simplification service with MockAIProvider
- Test that amounts, dates and eligibility conditions survive simplification
- Test abstention when passage is empty

**Manual demonstration required:**
- Upload PM-KISAN guidelines PDF
- Simplify the exclusion criteria passage
- Verify that the simplified version still mentions excluded categories

**Definition of done:** Endpoint live, frontend displays comparison, tests pass.

---

### Task 4.2 — Semantic Fidelity Evaluation Module

**Objective:** Detect whether a simplified or reformulated text preserves the semantic content of the source passage.

**Why needed:** This is CDTM dimension b. Without measurement, semantic fidelity is unverifiable.

**Suggested new files:**
- `app/evaluation/semantic_fidelity.py`
- `backend/tests/test_semantic_fidelity.py`

**Implementation approach:**
1. Define `SemanticFidelityResult` schema: `source_passage`, `transformed_text`, `preserved_conditions`, `potentially_omitted_conditions`, `fidelity_status`
2. Use AI provider to compare source and simplified texts for missing eligibility conditions, changed amounts, dropped exclusions
3. Return structured result — do not compute an arbitrary numeric score
4. Status: `"verified"`, `"potential_issue"`, `"requires_human_review"`

**Research integrity constraint:** Do not claim this evaluation is ground truth. It is itself an AI assessment and should be labelled as such.

**Acceptance criteria:** Module returns structured results; controlled failure demonstration (omitted exclusion) is detectable.

**Definition of done:** Module tested; controlled failure detected; integrated into CDTM dashboard in Phase 7.

---

### Task 4.3 — Controlled Failure Demonstration: Semantic Fidelity

**Objective:** Demonstrate a case where simplification omits a critical eligibility exclusion.

**Why needed:** Research demonstration of the type of failure CDTM aims to detect.

**Implementation approach:**
1. Prepare a source passage that includes an exclusion (e.g. "government employees are not eligible")
2. Create a deliberately incomplete simplified version that omits the exclusion
3. Run the semantic fidelity evaluator on this pair
4. Display the detected omission in the CDTM dashboard

**Important:** Label this clearly as a **controlled demonstration**, not a real-world finding.

---

## Phase 5 — Cross-Lingual Fidelity

### Task 5.1 — English-to-Hindi Translation Endpoint

**Objective:** Translate retrieved passages or generated answers from English to Hindi, preserving administrative terminology.

**Why needed:** Many Indian citizens are more comfortable in Hindi. Cross-Lingual Fidelity (CDTM dimension d) requires translation to be accurate.

**Relevant existing files:**
- `app/ai/base.py`
- `app/services/qa_service.py`

**Suggested new files:**
- `app/services/translation_service.py`

**Implementation approach:**
1. Add `translate_to_hindi(text, preserve_terms)` to AIProvider (or separate TranslationProvider interface)
2. System prompt must instruct model to preserve amounts (Rs 6,000), dates, scheme names, eligibility conditions verbatim or with standard transliteration
3. Return: `hindi_text`, `source_english_text`, `preserved_terms_check`
4. `POST /api/documents/{id}/translate` accepting `chunk_id` and `target_language="hi"`
5. Frontend bilingual display panel

**Suggested Git branch:** `feature/cross-lingual-fidelity`

**Acceptance criteria:**
- Hindi translation returned
- Financial amounts (e.g. Rs 6,000) appear unchanged or in Devanagari numerals
- Scheme names (PM-KISAN) appear in original form or standard transliteration
- Dates and deadlines are preserved

**Tests required:** MockAIProvider tests for translation service; amount/date preservation checks

**Definition of done:** Endpoint live, bilingual comparison view in frontend, tests pass.

---

### Task 5.2 — Cross-Lingual Fidelity Evaluation Module

**Objective:** Evaluate whether a translated text preserves the meaning of the English source.

**Suggested new files:**
- `app/evaluation/cross_lingual_fidelity.py`

**Implementation approach:**
1. Compare source English and Hindi translation for preserved amounts, dates, eligibility conditions
2. Use AI provider to back-translate Hindi to English and compare with source
3. Return structured result with identified divergences

**Research integrity constraint:** Back-translation comparison is an approximate method, not ground truth. All results must be labelled as AI-assisted assessments requiring human expert verification.

**Controlled failure demonstration:** Translate a passage; introduce an incorrect deadline in the Hindi version; verify the evaluator flags the divergence.

---

## Phase 6 — CDTM Evaluation Engine

This is the core research contribution. Each CDTM dimension requires a separate evaluation module.

### Task 6.1 — Source Fidelity Evaluator

**Objective:** Assess whether document extraction faithfully preserved the source content.

**What to check:**
- Were all pages extracted without text loss?
- Do chunk texts match the source PDF page exactly?
- Are there warnings from PyMuPDF (image-only pages)?
- Does the `source_fidelity_status` field reflect actual extraction quality?

**Relevant existing files:**
- `app/document/pdf_extractor.py` — already emits `warnings` list
- `app/api/routes.py` — `source_fidelity_status` placeholder already in response

**Suggested new files:**
- `app/evaluation/source_fidelity.py`
- `backend/tests/test_source_fidelity.py`

**Implementation approach:**
1. `SourceFidelityResult` schema: `page_count`, `pages_with_text`, `pages_without_text`, `warnings`, `status`
2. Status values: `"verified"` (all pages have text, no warnings), `"requires_review"` (warnings present), `"not_evaluated"` (default)
3. Surface result in API response and CDTM dashboard
4. Do not claim that "verified" means the extraction is semantically correct — only that selectable text was found

**Controlled failure demonstration:**
- Alter a financial amount in extracted text (in a controlled test fixture, not in real extraction)
- Show before and after comparison to illustrate what source fidelity failure looks like
- Label clearly as a demonstration, not a real event

**Acceptance criteria:** Evaluator returns structured result; image-only PDF pages trigger `"requires_review"` status; controlled demonstration is detectable.

**Tests required:** Test with text PDF (all pages pass), with mixed PDF (some pages flagged), and controlled failure fixture.

---

### Task 6.2 — Evidence Grounding Evaluator

**Objective:** Formally evaluate whether a generated answer is supported by the retrieved evidence.

**Note:** The citation validation in `qa_service.py` already performs basic grounding enforcement. This module makes the evaluation explicit and reportable.

**Relevant existing files:**
- `app/services/qa_service.py` — citation validation logic
- `app/ai/base.py` — GroundedAnswerResponse

**Suggested new files:**
- `app/evaluation/evidence_grounding.py`

**What to check:**
- Were citations valid (already done by backend validation)?
- Does the answer text make claims beyond what the retrieved passages state?
- Were any factual claims made without a corresponding citation?

**Implementation approach:**
1. `EvidenceGroundingResult` schema: `answer`, `cited_passages`, `uncited_claims` (AI-detected), `grounding_status`
2. Use AI provider to identify claims in the answer not supported by cited passages
3. Status: `"grounded"`, `"partially_grounded"`, `"ungrounded"`, `"abstained"`

**Controlled failure demonstration:**
- Provide a generated answer that claims a specific amount not mentioned in any retrieved passage
- Evaluator should flag the uncited claim

**Research integrity constraint:** The evaluator is itself an AI assessment. It should be presented as a detection aid, not as ground truth.

**Acceptance criteria:** Controlled failure is detected; grounded answer passes; abstention is recognised.

---

### Task 6.3 — Cross-Lingual Fidelity Evaluator

*(See Task 5.2)*

---

### Task 6.4 — Citizen Accessibility Evaluator

**Objective:** Assess whether generated explanations are understandable by a non-expert citizen.

**What to check:**
- Flesch-Kincaid readability score or equivalent
- Presence of undefined jargon or administrative terms
- Whether the explanation answers the citizen's practical question

**Implementation approach:**
1. Compute readability metrics (pure Python — no additional dependency needed for basic metrics)
2. Use AI provider to identify unexplained technical terms
3. `CitizenAccessibilityResult` schema: `readability_score`, `jargon_terms`, `practical_guidance_present`, `status`

**Research integrity constraint:** Readability scores are proxies, not validated measures of citizen comprehension. Empirical user study is required for genuine evaluation (Phase 9).

**Controlled failure demonstration:**
- Provide a technically correct answer written in formal administrative language
- Evaluator flags low readability and unexplained terms

---

## Phase 7 — CDTM Dashboard

### Task 7.1 — Frontend CDTM Dashboard Panel

**Objective:** Display all five CDTM dimension results in a clear, honest frontend panel.

**Why needed:** The research contribution requires a visible, transparent evaluation output.

**Suggested new files:**
- `frontend/src/components/CDTMDashboard.jsx`
- `frontend/src/components/DimensionCard.jsx`

**Backend requirements:** 
- New endpoint or extend existing to return all five dimension evaluations for a processed document
- `GET /api/documents/{id}/cdtm-evaluation` returning all five `*EvaluationResult` objects

**UI requirements:**
- Five cards, one per dimension
- Status labels: **Verified** (green), **Potential Issue** (amber), **Requires Human Review** (amber), **Not Evaluated** (grey)
- Supporting evidence panel (expandable) for each card
- No single overall trust score — only per-dimension statuses
- Clear label: "AI-assisted evaluation — results require human expert verification"

**Acceptance criteria:** All five dimensions display in frontend; controlled failure demonstrations show Potential Issue status; Verified shows for clean documents.

---

## Phase 8 — Complete Demonstration

### Task 8.1 — Comparative Demonstration View

**Objective:** Side-by-side comparison: "Basic AI Assistance" (answer only) vs "CDTM-Guided Assistance" (answer + all five evaluation dimensions).

**Why needed:** This is the primary research demonstration showing the value of CDTM.

**Implementation approach:**
1. Frontend toggle: Basic / CDTM-Guided mode
2. Basic mode: current Q&A panel only
3. CDTM-Guided mode: Q&A panel + CDTM dashboard
4. Phase progress indicators showing which pipeline stages have completed

**Acceptance criteria:** Toggle works; both modes functional; phases clearly labelled.

---

### Task 8.2 — Controlled Failure Demonstration Toggles

**Objective:** Allow the demonstrator to trigger each of the five controlled failure scenarios.

**Implementation approach:**
1. Backend: `POST /api/demo/trigger-failure` accepting `dimension` and `failure_type`
2. Each failure type returns a modified result showing the detected issue
3. Frontend: "Demo Controls" panel (clearly labelled as demonstration mode)

**Research integrity constraint:** Each controlled failure must be clearly labelled as a deliberately triggered demonstration, never presented as a real extraction or generation failure.

---

## Phase 9 — Validation and Study

### Task 9.1 — Document Corpus Selection

**Objective:** Select a set of authentic, publicly available Indian administrative documents for evaluation.

**Requirements:**
- Documents must be real, publicly available (from official government websites)
- Cover at least English and Hindi versions of the same content
- Include at least one document in a selected regional language
- Document types: welfare scheme guidelines, government notices, eligibility rules

**Research integrity constraint:** Do not fabricate documents or modify their content.

---

### Task 9.2 — Expert Evaluation

**Objective:** Have bilingual subject-matter experts review system outputs against source documents.

**Requirements:**
- Experts assess whether extractions, simplifications and translations preserve content faithfully
- Record actual expert findings — do not report hypothetical or expected results
- Disagreements between experts should be noted

---

### Task 9.3 — Citizen Comprehension Evaluation (if feasible)

**Objective:** Test whether target citizens can understand and use system outputs.

**Requirements:**
- Recruit participants representative of the intended user group
- Use standardised comprehension tasks
- Record and report actual results only
- Obtain appropriate ethical approval

**Research integrity constraint:** Do not report this evaluation as complete unless it has actually been conducted.

---

## Optional Future Work

These items are not required for the current research prototype but may be valuable longer-term.

| Item | Description | Effort |
|------|-------------|--------|
| **Persistent storage** | Replace in-memory store with SQLite or PostgreSQL | Medium |
| **OCR support** | Integrate Tesseract or cloud OCR for scanned PDFs | Medium–High |
| **Hybrid retrieval** | Combine BM25 with dense vector search (e.g. sentence-transformers) | High |
| **Additional AI providers** | Add Anthropic Claude, local Ollama, or others via AIProvider interface | Low–Medium per provider |
| **Local model support** | Ollama integration for air-gapped or cost-free operation | Medium |
| **Regional language support** | Extend beyond Hindi to Tamil, Telugu, Bengali, etc. | High |
| **Additional document formats** | DOCX, HTML government pages | Medium |
| **Session persistence** | LocalStorage or backend session for document/question history | Low |
| **Rate limiting and authentication** | Multi-user API protection | Medium |

---

## Recommended Implementation Order

For the **teacher demonstration**, the following must be done:

1. ✅ ~~Phase 1–3 core~~ (complete)
2. Push Groq integration to GitHub (Task 3.R1)
3. Real API integration test (Task 3.R2)
4. Source Fidelity evaluator (Task 6.1) — most important for demonstration
5. Evidence Grounding evaluator (Task 6.2) — directly builds on existing validation
6. CDTM Dashboard (Phase 7) — makes research visible
7. Comparative demonstration (Task 8.1) — the core demo moment
8. Controlled failure demonstrations (Task 8.2) — essential for research presentation

**Can safely be postponed:**
- Phases 4 and 5 (Semantic Fidelity and Cross-Lingual) — important research but not needed for minimum viable demo
- Phase 9 (Validation Study) — requires significant time and planning
- All Optional Future Work items

---

## Known Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Groq or Gemini rate limits during live demo | Medium | High | Test before demo; have backup offline demo mode |
| BM25 retrieval returning irrelevant chunks | Medium | Medium | Add minimum score threshold; show scores in UI |
| AI model generating uncited claims | Medium | High | Citation validation already in place; display clearly |
| PyMuPDF failing on complex PDFs | Low | Medium | Test with target demo documents in advance |
| In-memory store lost on restart | High (by design) | Medium | Re-upload documents; document clearly |
| Provider API key expiry or revocation | Low | High | Keep backup key; test before demo |

---

## Research Integrity Constraints

The following must be maintained throughout development:

1. **Never fabricate metrics.** All reported evaluation results must come from actual runs, not hypothetical scenarios.
2. **Never claim empirical validation has occurred unless it has.** CDTM is a proposed framework; this prototype demonstrates it, not validates it.
3. **Mark all controlled failures as demonstrations.** Never present a deliberately triggered failure as a real system failure.
4. **Maintain CDTM terminology as defined.** Do not redefine dimensions mid-project.
5. **Citation validation does not equal factual verification.** Be precise about what has and has not been verified.
6. **Citizen Accessibility cannot be claimed without a user study.** Label the accessibility evaluator as a proxy measure.

---

## Suggested Git Branch Names

| Work | Suggested Branch |
|------|-----------------|
| Groq push | `feature/groq-integration` |
| Semantic Fidelity | `feature/semantic-fidelity` |
| Cross-Lingual | `feature/cross-lingual-fidelity` |
| Source Fidelity evaluator | `feature/cdtm-source-fidelity` |
| Evidence Grounding evaluator | `feature/cdtm-evidence-grounding` |
| Citizen Accessibility evaluator | `feature/cdtm-accessibility` |
| CDTM Dashboard | `feature/cdtm-dashboard` |
| Demo mode | `feature/demonstration-mode` |
| Persistent storage | `feature/persistent-storage` |
| OCR support | `feature/ocr-support` |

---

## Immediate Next Steps for the New Developer

1. **Get collaborator access** to https://github.com/abhigyan-21/CitizenAssistAI
2. **Clone main** and confirm you can run the backend tests (47 tests, all pass)
3. **Set up local `.env`** with your Groq API key (free tier at https://console.groq.com)
4. **Confirm Groq integration** is in the codebase — if `app/ai/groq.py` does not exist, the original developer has not yet pushed it; request the files or the push
5. **Run the real Groq integration test** (Task 3.R2) with a public Indian government PDF
6. **Read CDTM definitions** in `PROJECT_HANDOVER.md` Section 2 before implementing any evaluation module
7. **Start Phase 6** with the Source Fidelity evaluator (Task 6.1) — it builds directly on existing extraction output

---

*Document prepared for engineering handover — CitizenAssist AI, 2026-11-18*
