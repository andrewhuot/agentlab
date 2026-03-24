"""Unit tests for bandit-based experiment selection."""

from __future__ import annotations

import random

from optimizer.bandit import ArmStats, BanditPolicy, BanditSelector


# ---------------------------------------------------------------------------
# ArmStats property tests
# ---------------------------------------------------------------------------


class TestArmStats:
    def test_mean_reward_zero_attempts(self) -> None:
        arm = ArmStats(arm_id="a::b", operator_name="a", failure_family="b")
        assert arm.mean_reward == 0.0

    def test_mean_reward_with_data(self) -> None:
        arm = ArmStats(
            arm_id="a::b",
            operator_name="a",
            failure_family="b",
            attempts=4,
            total_reward=2.0,
        )
        assert abs(arm.mean_reward - 0.5) < 1e-9

    def test_success_rate_zero_attempts_returns_optimistic_prior(self) -> None:
        arm = ArmStats(arm_id="a::b", operator_name="a", failure_family="b")
        assert arm.success_rate == 0.5

    def test_success_rate_with_data(self) -> None:
        arm = ArmStats(
            arm_id="a::b",
            operator_name="a",
            failure_family="b",
            attempts=10,
            successes=7,
        )
        assert abs(arm.success_rate - 0.7) < 1e-9


# ---------------------------------------------------------------------------
# UCB1 selection tests
# ---------------------------------------------------------------------------


class TestUCB1Selection:
    def test_unvisited_arms_prioritized(self) -> None:
        """UCB1 should always select an unvisited arm first."""
        selector = BanditSelector(policy=BanditPolicy.ucb1)
        # Record some history for arm A
        selector.record_outcome("op_a", "fam_x", True, reward=1.0)
        selector.record_outcome("op_a", "fam_x", True, reward=1.0)

        candidates = [("op_a", "fam_x"), ("op_b", "fam_y")]
        selected = selector.select(candidates)
        # op_b::fam_y has never been tried, so it should be selected
        assert selected == ("op_b", "fam_y")

    def test_explores_low_count_arms(self) -> None:
        """UCB1 exploration bonus should favor arms tried fewer times."""
        selector = BanditSelector(policy=BanditPolicy.ucb1)
        # arm A: pulled many times with modest reward
        for _ in range(50):
            selector.record_outcome("op_a", "fam", False, reward=0.1)
        # arm B: pulled once with same reward
        selector.record_outcome("op_b", "fam", False, reward=0.1)

        candidates = [("op_a", "fam"), ("op_b", "fam")]
        selected = selector.select(candidates)
        # With fewer pulls, arm B should have a larger exploration bonus
        assert selected == ("op_b", "fam")

    def test_exploits_high_reward_arm(self) -> None:
        """UCB1 should favor high-reward arms when exploration term is small."""
        selector = BanditSelector(policy=BanditPolicy.ucb1, exploration_weight=0.01)
        # arm A: high reward
        for _ in range(20):
            selector.record_outcome("op_a", "fam", True, reward=1.0)
        # arm B: low reward
        for _ in range(20):
            selector.record_outcome("op_b", "fam", False, reward=0.0)

        candidates = [("op_a", "fam"), ("op_b", "fam")]
        selected = selector.select(candidates)
        assert selected == ("op_a", "fam")

    def test_empty_candidates_raises(self) -> None:
        selector = BanditSelector(policy=BanditPolicy.ucb1)
        try:
            selector.select([])
            assert False, "Expected ValueError"
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Thompson Sampling tests
# ---------------------------------------------------------------------------


class TestThompsonSelection:
    def test_selects_from_candidates(self) -> None:
        """Thompson sampling should return one of the candidates."""
        random.seed(42)
        selector = BanditSelector(policy=BanditPolicy.thompson)
        candidates = [("op_a", "fam_x"), ("op_b", "fam_y")]
        selected = selector.select(candidates)
        assert selected in candidates

    def test_favors_successful_arm_over_many_trials(self) -> None:
        """Over many selections, Thompson should favor the arm with higher success rate."""
        random.seed(123)
        selector = BanditSelector(policy=BanditPolicy.thompson)
        # arm A: 90% success
        for _ in range(100):
            selector.record_outcome("op_a", "fam", True)
        for _ in range(11):
            selector.record_outcome("op_a", "fam", False)
        # arm B: 10% success
        for _ in range(11):
            selector.record_outcome("op_b", "fam", True)
        for _ in range(100):
            selector.record_outcome("op_b", "fam", False)

        candidates = [("op_a", "fam"), ("op_b", "fam")]
        selections = {"op_a": 0, "op_b": 0}
        for _ in range(200):
            op, _ = selector.select(candidates)
            selections[op] += 1

        # arm A should be selected much more often
        assert selections["op_a"] > selections["op_b"]


# ---------------------------------------------------------------------------
# Outcome recording tests
# ---------------------------------------------------------------------------


class TestRecordOutcome:
    def test_updates_stats(self) -> None:
        selector = BanditSelector()
        selector.record_outcome("op_a", "fam_x", True, reward=0.5)
        selector.record_outcome("op_a", "fam_x", False, reward=-0.1)

        arm = selector.get_or_create_arm("op_a", "fam_x")
        assert arm.attempts == 2
        assert arm.successes == 1
        assert abs(arm.total_reward - 0.4) < 1e-9
        assert selector._total_pulls == 2

    def test_separate_arms_tracked_independently(self) -> None:
        selector = BanditSelector()
        selector.record_outcome("op_a", "fam_x", True, reward=1.0)
        selector.record_outcome("op_b", "fam_y", False, reward=0.0)

        arm_a = selector.get_or_create_arm("op_a", "fam_x")
        arm_b = selector.get_or_create_arm("op_b", "fam_y")
        assert arm_a.successes == 1
        assert arm_b.successes == 0


# ---------------------------------------------------------------------------
# rank_candidates tests
# ---------------------------------------------------------------------------


class TestRankCandidates:
    def test_returns_ordered_list(self) -> None:
        selector = BanditSelector(policy=BanditPolicy.ucb1)
        # Give arm A high reward
        for _ in range(10):
            selector.record_outcome("op_a", "fam", True, reward=1.0)
        # Give arm B low reward
        for _ in range(10):
            selector.record_outcome("op_b", "fam", False, reward=0.0)

        candidates = [("op_a", "fam"), ("op_b", "fam")]
        ranked = selector.rank_candidates(candidates, n=2)
        assert len(ranked) == 2
        # First should have higher score
        assert ranked[0][2] >= ranked[1][2]
        assert ranked[0][0] == "op_a"

    def test_unvisited_arms_get_infinity_score(self) -> None:
        selector = BanditSelector(policy=BanditPolicy.ucb1)
        candidates = [("op_new", "fam")]
        ranked = selector.rank_candidates(candidates, n=1)
        assert len(ranked) == 1
        assert ranked[0][2] == float("inf")

    def test_n_caps_results(self) -> None:
        selector = BanditSelector(policy=BanditPolicy.ucb1)
        candidates = [("op_a", "fam"), ("op_b", "fam"), ("op_c", "fam")]
        ranked = selector.rank_candidates(candidates, n=2)
        assert len(ranked) == 2

    def test_thompson_ranking_uses_mean(self) -> None:
        selector = BanditSelector(policy=BanditPolicy.thompson)
        # arm A: 9 successes out of 10
        for _ in range(9):
            selector.record_outcome("op_a", "fam", True)
        selector.record_outcome("op_a", "fam", False)
        # arm B: 1 success out of 10
        selector.record_outcome("op_b", "fam", True)
        for _ in range(9):
            selector.record_outcome("op_b", "fam", False)

        candidates = [("op_a", "fam"), ("op_b", "fam")]
        ranked = selector.rank_candidates(candidates, n=2)
        # Thompson ranking uses alpha/(alpha+beta) mean, so op_a should rank first
        assert ranked[0][0] == "op_a"


# ---------------------------------------------------------------------------
# get_arm_stats tests
# ---------------------------------------------------------------------------


class TestGetArmStats:
    def test_returns_sorted_by_mean_reward(self) -> None:
        selector = BanditSelector()
        selector.record_outcome("op_a", "fam", True, reward=0.5)
        selector.record_outcome("op_b", "fam", True, reward=1.0)
        selector.record_outcome("op_c", "fam", True, reward=0.2)

        stats = selector.get_arm_stats()
        assert len(stats) == 3
        assert stats[0].operator_name == "op_b"
        assert stats[-1].operator_name == "op_c"

    def test_empty_selector_returns_empty(self) -> None:
        selector = BanditSelector()
        assert selector.get_arm_stats() == []
