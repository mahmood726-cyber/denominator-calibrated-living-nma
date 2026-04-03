from __future__ import annotations


def coverage_rate(intervals: list[tuple[float, float]], truths: list[float]) -> float:
    if len(intervals) != len(truths):
        raise ValueError("Intervals and truths must have the same length.")
    if not truths:
        return 0.0
    covered = sum(1 for (lower, upper), truth in zip(intervals, truths) if lower <= truth <= upper)
    return covered / len(truths)


def false_reassurance_rate(decisions: list[str], truths: list[float]) -> float:
    if len(decisions) != len(truths):
        raise ValueError("Decisions and truths must have the same length.")
    if not truths:
        return 0.0
    false_reassurance = sum(
        1 for decision, truth in zip(decisions, truths) if decision == "recommend" and truth >= 0
    )
    return false_reassurance / len(truths)


def mean_decision_regret(
    decisions: list[str],
    truths: list[float],
    false_positive_weight: float = 1.0,
    false_negative_weight: float = 2.0,
    research_penalty: float = 0.5,
) -> float:
    if len(decisions) != len(truths):
        raise ValueError("Decisions and truths must have the same length.")
    if not truths:
        return 0.0

    regret_total = 0.0
    for decision, truth in zip(decisions, truths):
        if decision == "recommend" and truth >= 0:
            regret_total += false_positive_weight
        elif decision == "do_not_use" and truth < 0:
            regret_total += false_negative_weight
        elif decision == "research":
            regret_total += research_penalty
    return regret_total / len(truths)
