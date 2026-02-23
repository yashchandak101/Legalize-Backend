# AI guidance

This folder holds instructions and conventions for AI assistants (e.g. Cursor) working on the Legalize project.

## Contents

| File | Purpose |
|------|--------|
| **agents.md** | Main agent instructions: project overview, layout, conventions, where to add code, how to run tests. Use this as the primary context when editing the repo. |
| **backend-conventions.md** | Backend-only details: Flask/SQLAlchemy patterns, layers, IDs, datetimes, testing fixtures, AI integration. |
| **coding-standards.md** | Python/style: imports, types, errors, datetimes, structure, tests. |
| **constraints.md** | Hard rules: UUIDs, roles, appointment status flow, permissions, no secrets in code. |
| **domain-rules.md** | Business rules: appointment status lifecycle, who can do what, upcoming definition. |
| **prompting-rules.md** | How to prompt AI for this project: scope, where to put code, tests, conventions. |
| **README.md** | This file – describes the folder. |

## Current Implementation Status

### ✅ Completed Phases
- **Phase 1**: Foundation (Users, Cases, Appointments)
- **Phase 2**: Lawyer Profiles & Case Assignments  
- **Phase 3**: Comments & Documents
- **Phase 4**: Payments & Notifications
- **Phase 5**: AI & Background Workers

### 🔄 Current Features
- **AI Legal Engine**: Case suggestions and document analysis
- **Background Workers**: Celery + Redis for async processing
- **Payment Processing**: Stripe integration with webhooks
- **Notifications**: In-app notifications with event triggers
- **Document Management**: File upload/download with AI analysis
- **Role-Based Access**: Users, Lawyers, Admins with proper permissions

### � Future AI Roadmap
- **Phase 6**: Advanced AI Features (Legal research automation)
- **Phase 7**: Multi-modal AI (Text, voice, document analysis)
- **Phase 8**: Custom AI model fine-tuning for legal domain

---

*Last updated: February 2026*
