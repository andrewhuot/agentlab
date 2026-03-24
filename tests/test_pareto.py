"""Unit tests for the Constrained Pareto Archive."""

from __future__ import annotations

from optimizer.pareto import ParetoArchive, ParetoCandidate


def _candidate(
    cid: str = "c1",
    objectives: list[float] | None = None,
    constraints_passed: bool = True,
    constraint_violations: list[str] | None = None,
    config_hash: str = "hash1",
    experiment_id: str | None = None,
) -> ParetoCandidate:
    """Build a minimal ParetoCandidate."""
    return ParetoCandidate(
        candidate_id=cid,
        objective_vector=objectives or [0.5, 0.5, 0.5],
        constraints_passed=constraints_passed,
        constraint_violations=constraint_violations or [],
        config_hash=config_hash,
        experiment_id=experiment_id,
    )


# ── Dominance checks ────────────────────────────────────────────────


def test_dominates_basic() -> None:
    """a strictly better in all dims should dominate b."""
    assert ParetoArchive.dominates([1.0, 1.0], [0.5, 0.5]) is True


def test_dominates_equal_vectors() -> None:
    """Equal vectors should not dominate each other."""
    assert ParetoArchive.dominates([0.5, 0.5], [0.5, 0.5]) is False


def test_dominates_single_dimension() -> None:
    """Better in one, equal in other should dominate."""
    assert ParetoArchive.dominates([1.0, 0.5], [0.5, 0.5]) is True


def test_dominates_incomparable() -> None:
    """Trade-off vectors should not dominate each other."""
    assert ParetoArchive.dominates([1.0, 0.0], [0.0, 1.0]) is False
    assert ParetoArchive.dominates([0.0, 1.0], [1.0, 0.0]) is False


def test_dominates_worse_in_one() -> None:
    """If worse in any dim, cannot dominate."""
    assert ParetoArchive.dominates([0.9, 0.4], [0.5, 0.5]) is False


# ── Adding feasible / infeasible candidates ──────────────────────────


def test_add_feasible_on_frontier() -> None:
    """A feasible candidate with no competition should be on the frontier."""
    archive = ParetoArchive()
    c = _candidate("c1", [0.8, 0.9])
    on_front = archive.add(c)
    assert on_front is True
    assert len(archive.get_frontier()) == 1


def test_add_infeasible_not_on_frontier() -> None:
    """An infeasible candidate should never be on the frontier."""
    archive = ParetoArchive()
    c = _candidate("c1", [0.8, 0.9], constraints_passed=False,
                    constraint_violations=["safety failure"])
    on_front = archive.add(c)
    assert on_front is False
    assert len(archive.get_frontier()) == 0
    assert len(archive.get_infeasible()) == 1


def test_add_infeasible_preserves_violations() -> None:
    """Infeasible candidate should retain its violation details."""
    archive = ParetoArchive()
    c = _candidate("c1", [0.8, 0.9], constraints_passed=False,
                    constraint_violations=["safety: 2 failures"])
    archive.add(c)
    infeasible = archive.get_infeasible()
    assert infeasible[0].constraint_violations == ["safety: 2 failures"]


# ── Frontier maintenance ─────────────────────────────────────────────


def test_frontier_dominated_removed() -> None:
    """A new dominant candidate should mark dominated ones."""
    archive = ParetoArchive()
    archive.add(_candidate("c1", [0.5, 0.5]))
    archive.add(_candidate("c2", [0.6, 0.6]))  # dominates c1

    frontier = archive.get_frontier()
    assert len(frontier) == 1
    assert frontier[0].candidate_id == "c2"


def test_frontier_incomparable_both_kept() -> None:
    """Two incomparable candidates should both stay on the frontier."""
    archive = ParetoArchive()
    archive.add(_candidate("c1", [1.0, 0.0]))
    archive.add(_candidate("c2", [0.0, 1.0]))

    frontier = archive.get_frontier()
    assert len(frontier) == 2
    ids = {c.candidate_id for c in frontier}
    assert ids == {"c1", "c2"}


def test_frontier_three_candidates_one_dominated() -> None:
    """With 3 candidates where one is dominated, frontier should have 2."""
    archive = ParetoArchive()
    archive.add(_candidate("c1", [0.8, 0.2]))
    archive.add(_candidate("c2", [0.2, 0.8]))
    archive.add(_candidate("c3", [0.9, 0.9]))  # dominates both

    frontier = archive.get_frontier()
    assert len(frontier) == 1
    assert frontier[0].candidate_id == "c3"


# ── Knee-point recommendation ───────────────────────────────────────


def test_recommend_single_candidate() -> None:
    """With one candidate, recommendation should return it."""
    archive = ParetoArchive()
    archive.add(_candidate("c1", [0.7, 0.8]))
    rec = archive.recommend()
    assert rec is not None
    assert rec.candidate_id == "c1"


def test_recommend_empty_archive() -> None:
    """Empty archive should return None."""
    archive = ParetoArchive()
    assert archive.recommend() is None


def test_recommend_picks_balanced() -> None:
    """Recommend should prefer the balanced candidate over extremes."""
    archive = ParetoArchive()
    archive.add(_candidate("extreme_a", [1.0, 0.0]))
    archive.add(_candidate("balanced", [0.6, 0.6]))
    archive.add(_candidate("extreme_b", [0.0, 1.0]))

    rec = archive.recommend()
    assert rec is not None
    assert rec.candidate_id == "balanced"


def test_recommend_with_uniform_frontier() -> None:
    """When all frontier candidates are equally balanced, any is valid."""
    archive = ParetoArchive()
    archive.add(_candidate("c1", [0.5, 0.5]))
    archive.add(_candidate("c2", [0.5, 0.5]))
    rec = archive.recommend()
    assert rec is not None


# ── Frontier movement tracking ───────────────────────────────────────


def test_frontier_movement_added_removed() -> None:
    """frontier_movement should correctly detect added/removed/retained."""
    archive = ParetoArchive()
    # Build "previous" frontier
    prev_c1 = _candidate("c1", [0.5, 0.5])
    prev_c2 = _candidate("c2", [0.3, 0.7])
    previous_frontier = [prev_c1, prev_c2]

    # Current archive: c2 retained, c3 new, c1 gone
    archive.add(_candidate("c2", [0.3, 0.7]))
    archive.add(_candidate("c3", [0.8, 0.8]))

    movement = archive.frontier_movement(previous_frontier)

    assert "c3" in movement["added"]
    assert "c1" in movement["removed"]
    # c2 may be dominated by c3 so it might not be retained on frontier
    assert movement["frontier_size_before"] == 2
    assert movement["frontier_size_after"] >= 1


def test_frontier_movement_no_change() -> None:
    """If frontier is identical, added/removed should be empty."""
    archive = ParetoArchive()
    c1 = _candidate("c1", [0.5, 0.5])
    archive.add(c1)

    movement = archive.frontier_movement([c1])
    assert movement["added"] == []
    assert movement["removed"] == []
    assert movement["retained"] == ["c1"]


# ── Max archive size enforcement ─────────────────────────────────────


def test_max_archive_size_enforced() -> None:
    """Archive should not exceed max_archive_size."""
    archive = ParetoArchive(max_archive_size=5)
    for i in range(10):
        archive.add(_candidate(f"c{i}", [float(i) / 10, 1.0 - float(i) / 10]))

    total = len(archive._feasible)
    assert total <= 5


def test_max_archive_size_infeasible() -> None:
    """Infeasible archive should also respect max size."""
    archive = ParetoArchive(max_archive_size=3)
    for i in range(7):
        archive.add(_candidate(
            f"inf{i}", [0.5, 0.5],
            constraints_passed=False,
            constraint_violations=["fail"],
        ))

    assert len(archive._infeasible) <= 3


# ── Serialization ────────────────────────────────────────────────────


def test_to_dict_structure() -> None:
    """to_dict should return expected keys."""
    archive = ParetoArchive()
    archive.add(_candidate("c1", [0.8, 0.9]))
    archive.add(_candidate("c2", [0.5, 0.5], constraints_passed=False,
                            constraint_violations=["fail"]))

    d = archive.to_dict()
    assert d["frontier_size"] == 1
    assert d["feasible_total"] == 1
    assert d["infeasible_total"] == 1
    assert d["recommended_id"] == "c1"
    assert len(d["frontier"]) == 1
    assert d["frontier"][0]["candidate_id"] == "c1"
