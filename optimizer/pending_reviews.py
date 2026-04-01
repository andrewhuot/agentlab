"""JSON-backed persistence for pending optimization review proposals."""

from __future__ import annotations

import json
from pathlib import Path

from api.models import PendingReview


class PendingReviewStore:
    """Persist pending optimization reviews so approval survives restarts.

    WHY: optimization proposals can require explicit human approval before
    deployment, so the server needs a durable queue that is cheap to inspect
    and easy to recover after a restart.
    """

    def __init__(self, store_dir: str = "workspace/pending_reviews") -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _review_path(self, attempt_id: str) -> Path:
        """Return the on-disk path for one pending review.

        WHY: one-file-per-review keeps writes atomic and makes manual debugging
        straightforward when operators inspect the workspace.
        """

        return self.store_dir / f"{attempt_id}.json"

    def save_review(self, review: PendingReview) -> None:
        """Persist or replace one pending review record.

        WHY: the optimize route writes the candidate once it passes gates so the
        later approval flow can reuse the exact proposed config and score payload.
        """

        payload = review.model_dump(mode="json")
        self._review_path(review.attempt_id).write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def list_pending(self, limit: int = 50) -> list[PendingReview]:
        """Return pending reviews ordered newest first.

        WHY: operators care most about the latest candidate proposals when the
        UI refreshes, so list views should naturally surface recent items first.
        """

        reviews: list[PendingReview] = []
        for path in sorted(
            self.store_dir.glob("*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        ):
            payload = json.loads(path.read_text(encoding="utf-8"))
            reviews.append(PendingReview.model_validate(payload))
            if len(reviews) >= limit:
                break
        return reviews

    def get_review(self, attempt_id: str) -> PendingReview | None:
        """Load one pending review by attempt id.

        WHY: approval and rejection actions must resolve the exact review record
        that the optimize loop persisted earlier.
        """

        path = self._review_path(attempt_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return PendingReview.model_validate(payload)

    def delete_review(self, attempt_id: str) -> bool:
        """Delete one pending review if it exists.

        WHY: once a human approves or rejects a proposal, it should leave the
        queue immediately so operators do not reprocess stale candidates.
        """

        path = self._review_path(attempt_id)
        if not path.exists():
            return False
        path.unlink()
        return True
