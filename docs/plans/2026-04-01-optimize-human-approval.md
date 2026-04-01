# Optimize Human Approval Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a human-in-the-loop review step for optimizer proposals so accepted candidates default to `pending_review` instead of auto-deploying.

**Architecture:** Extend the optimize request model and optimize route to branch between auto-deploy and review-queue behavior. Persist pending reviews as JSON files in a workspace-local directory, expose list/approve/reject endpoints, and update the Optimize page to surface pending cards, approval actions, and a default-on toggle.

**Tech Stack:** FastAPI, Pydantic, JSON file persistence, React, TanStack Query, Vitest, Vite

---

### Task 1: Plan The Backend Review Queue

**Files:**
- Modify: `api/models.py`
- Modify: `api/routes/optimize.py`
- Modify: `api/server.py`
- Create: `optimizer/pending_reviews.py`
- Test: `tests/test_optimize_api.py`

**Step 1: Write the failing backend tests**

Add tests that prove:
- `OptimizeRequest` defaults `require_human_approval` to `True`
- accepted optimize runs with approval enabled create a pending review and do not call `deployer.deploy()`
- `/api/optimize/pending` lists persisted review payloads
- `/api/optimize/pending/{attempt_id}/approve` deploys through the same deployer path and removes the pending review
- `/api/optimize/pending/{attempt_id}/reject` removes the pending review without deploying

**Step 2: Run the backend tests to verify they fail**

Run: `pytest tests/test_optimize_api.py -q`
Expected: FAIL because the review queue model/store/routes do not exist yet.

**Step 3: Implement the pending review models and store**

Add:
- request flag in `OptimizeRequest`
- Pydantic response/data models for pending reviews
- a small JSON-backed store with `save`, `list_pending`, `get`, and `delete`

**Step 4: Wire optimize route behavior**

Update `/api/optimize/run` to:
- evaluate the candidate as it does today
- on accepted candidates with `require_human_approval=True`, skip deploy, persist pending review context, return a `Pending human review` status, and emit `optimize_pending_review`
- on accepted candidates with `require_human_approval=False`, preserve current deploy behavior

**Step 5: Add approval and rejection routes**

Implement:
- `GET /api/optimize/pending`
- `POST /api/optimize/pending/{attempt_id}/approve`
- `POST /api/optimize/pending/{attempt_id}/reject`

**Step 6: Re-run backend tests**

Run: `pytest tests/test_optimize_api.py -q`
Expected: PASS

### Task 2: Add Optimize Page Review UI

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/pages/Optimize.tsx`
- Test: `web/src/pages/Optimize.test.tsx`

**Step 1: Write the failing frontend tests**

Add tests that prove:
- the optimize start payload includes `require_human_approval: true` by default
- pending review cards render above history with reasoning, score movement, and diff
- approving a review triggers the approve mutation and success toast
- rejecting a review triggers the reject mutation and info toast
- starting a new optimization while pending reviews exist shows a warning

**Step 2: Run the page tests to verify they fail**

Run: `cd web && npx vitest run src/pages/Optimize.test.tsx`
Expected: FAIL because the types/hooks/UI do not exist yet.

**Step 3: Implement types and hooks**

Add `PendingReview` and the React Query hooks for list/approve/reject.

**Step 4: Update the page**

Add:
- default-on human approval toggle in the main run controls
- pending review cards above history
- approve/reject actions with optimistic refreshes and toasts
- websocket refresh on `optimize_pending_review`
- warning toast when starting another optimization while reviews are still queued

**Step 5: Re-run the page tests**

Run: `cd web && npx vitest run src/pages/Optimize.test.tsx`
Expected: PASS

### Task 3: Verify And Ship

**Files:**
- Review: git diff for all touched files

**Step 1: Run required verification**

Run:
- `pytest tests/test_optimize_api.py -q`
- `cd web && npx vitest run src/pages/Optimize.test.tsx`
- `cd web && npx tsc --noEmit`
- `cd web && npx vite build`

**Step 2: Review the diff**

Run: `git diff -- docs/plans/2026-04-01-optimize-human-approval.md api/models.py api/routes/optimize.py api/server.py optimizer/pending_reviews.py tests/test_optimize_api.py web/src/lib/types.ts web/src/lib/api.ts web/src/pages/Optimize.tsx web/src/pages/Optimize.test.tsx`

**Step 3: Commit**

Run:
```bash
git add docs/plans/2026-04-01-optimize-human-approval.md api/models.py api/routes/optimize.py api/server.py optimizer/pending_reviews.py tests/test_optimize_api.py web/src/lib/types.ts web/src/lib/api.ts web/src/pages/Optimize.tsx web/src/pages/Optimize.test.tsx
git commit -m "feat(optimize): human-in-the-loop approval for optimization proposals"
```

**Step 4: Push**

Run: `git push origin master`

**Step 5: Send completion event**

Run: `openclaw system event --text "Done: Human approval flow for optimization — review before deploy" --mode now`
