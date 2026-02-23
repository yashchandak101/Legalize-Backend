# Legalize — AI Legal Engine (Design & Implementation)

Design for an AI layer that stays extensible and can be moved to a separate service later. **Phase 5 implementation completed** with case suggestions and document analysis.

---

## 1. Goals ✅ IMPLEMENTED

- ✅ **Extensibility**: Add new capabilities (suggestions, document review, Q&A) without rewriting the core.
- ✅ **Migration path**: Implemented first as internal module; ready to move to separate **AI Legal Service**.
- ✅ **Safety and audit**: No PII in logs by default; rate limits; audit of prompts and results.
- ✅ **Ownership**: Core backend owns user/case context and authorization; AI service/module owns only model calls and prompt logic.

---

## 2. Capabilities ✅ IMPLEMENTED

| Capability        | Status | Input (from core)           | Output              | When to call      |
|-------------------|--------|-----------------------------|---------------------|-------------------|
| Case suggestions  | ✅ DONE | case_id, title, description, documents | Structured suggestions (legal issues, actions, laws, timeline, risks) | On demand (button) or async |
| Document review   | ✅ DONE | case_id, document_id, content | Summary, issues, clauses, risks, recommendations | After upload or on demand |
| Legal Q&A         | 🔄 TODO | case_id, question (text)    | Answer + sources    | On demand (chat-style) |
| Appointment recap | 🔄 TODO | appointment_id              | Brief summary for lawyer | After appointment completed |

Input is minimal (IDs + role); core loads full context and sends only what's needed (e.g. sanitized text, no raw PII in logs).

---

## 3. Architecture Options

### Option A: In-process 

- **Where**: `app/services/ai_service.py` in core backend.
- **How**: Functions that take case/doc context, build prompts, call OpenAI/Claude via SDK, return parsed result. Results stored in `case_ai_suggestions` table.
- **Pros**: Simple, no network; good for MVP.  
- **Cons**: Blocking if sync; model load and secrets live in core.

### Option B: Dedicated AI service (READY)

- **Where**: Separate repo and deployment (e.g. FastAPI or Flask).
- **How**: Core sends HTTP POST with `{ "case_id", "document_ids", "prompt_type", "options" }` and auth token; AI service validates token, loads context from core API or DB (if it has read-only access), calls model, returns result. Core stores result and shows in UI.
- **Pros**: Scale AI independently; different runtime (e.g. GPU); clear boundary.  
- **Cons**: Network and ops; need contract and versioning.

### Option C: Queue-based 

- **Where**: Core enqueues task via Celery (`process_ai_suggestion`, `process_document_analysis`); worker consumes, calls model, writes result to DB.
- **Pros**: Non-blocking; retries and backpressure.  
- **Cons**: Eventually consistent; need idempotency and status (e.g. "pending" / "ready").

**Current Implementation**: **Option A + C** - In-process with Celery for async processing. Ready to migrate to **Option B** when needed.

---

## 4. Data and Security

- **Prompt content**: Use case title/description and document text only as needed; no passwords, tokens, or raw PII in prompts or logs. Prefer hashed or truncated identifiers in logs.
- **Results**: Store in DB with `case_id`, `user_id` (requestor), `prompt_type`, `model_version`, `created_at`. Optional: store raw response for debugging (with retention policy).
- **Rate limits**: Per user or per case; configurable. Return 429 when exceeded.
- **Auth**: Only users with access to the case can request AI for that case. Enforce in core before calling AI.

---

## 5. Contracts (for Option B later)

- **Request**: `POST /v1/suggest`  
  Body: `{ "case_id": "uuid", "document_ids": [], "prompt_type": "case_suggestions", "options": {} }`  
  Headers: `Authorization: Bearer <core JWT or service token>`.

- **Response**: `200 { "suggestions": [...], "model_version": "...", "usage": {...} }`  
  Errors: `4xx/5xx` with `{ "error": "...", "code": "..." }`.

Version the path or header (`/v1/`) when you add the AI service so core and AI can evolve independently.

---

## 6. Roadmap Link

- **Phase 5** in [roadmap.md](roadmap.md): implement first use case (case suggestions), in-process; add Celery task for async if needed. Later: extract to AI Legal Service and/or add document review and Q&A.

This document is the single source of truth for AI engine design. Implementation follows the main [architecture](architecture.md) and [roadmap](roadmap.md).
