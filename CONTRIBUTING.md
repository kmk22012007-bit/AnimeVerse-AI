# Contributing to AnimeVerse AI

Welcome to the **AnimeVerse AI** project. We appreciate community contributions to help improve our anime discovery, tracking, and social platform.

---

## Guidelines for Contributions

### 1. Repository Workflow
- Fork the repository and create your feature branch from `master`.
- Use descriptive branch names: `feature/<name>` or `fix/<name>`.
- Keep commits focused on a single topic with clear commit summaries.

### 2. Architecture & Code Conventions
- **Django Backend**:
  - Keep business and filtering logic within dedicated service classes (`backend/apps/*/services.py`).
  - Strict Content Filtering: All anime retrieval must respect `apps/anime/content_filter.py` to prevent NSFW leakage.
  - Session Authentication: Rely on `AnimeverseSessionMiddleware` for guest and profile identification.
  - Model Security: Disallow mass-assignment of `is_staff` or `role` fields in profile serializers.
- **React Frontend**:
  - Maintain the cyberpunk dark theme aesthetics using Tailwind CSS (`bg-gray-950`, neon borders).
  - API requests must route through `frontend/src/api/` helper clients.
  - UI components must be fully responsive across mobile (360px) to desktop (1080p+).

### 3. Verification & Testing
Before submitting a pull request, run the test suites:
- **Backend Tests**: `pytest backend/tests/ -v` (All 211 tests must pass).
- **Frontend Build**: `npm --prefix frontend run build` (Must build with 0 errors).
- **Django Configuration**: `python backend/manage.py check`.

### 4. Pull Request Submission
- Open a PR targeting the `master` branch.
- Complete the items in the pull request template.
- Attach visual evidence or screenshots for UI modifications.

### 5. Reporting Security Vulnerabilities
Do not open public GitHub issues for security vulnerabilities or credential exposures. Instead, email the repository maintainer privately.
