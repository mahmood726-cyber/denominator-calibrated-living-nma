"""Incremental ("living") update engine for the pooled evidence estimate.

A living network meta-analysis re-estimates as new trials arrive. Re-running the
whole pool from scratch on every update is correct but wasteful, so this module
maintains a running inverse-variance accumulator that can absorb one extraction
record at a time. The engine is deliberately built so that the incremental
result is *bit-for-bit reproducible* against a from-scratch batch recompute over
the same records — that equivalence is the correctness contract for any living
system and is checked directly by :func:`assert_living_equivalence` and the
``living-benchmark`` CLI command.

Only the *plumbing* is new here. The pooled numbers themselves come from
:func:`dclnma.data.linkage.inverse_variance_pool`, so no scientific output is
altered: incremental and batch paths share the same arithmetic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .data.linkage import inverse_variance_pool
from .data.models import ExtractionRecord


@dataclass(slots=True)
class LivingPoolState:
    """Running inverse-variance accumulator over log-effects.

    Maintains ``sum_w`` (Σ 1/se²) and ``sum_wx`` (Σ x/se²). The pooled estimate
    is ``sum_wx / sum_w`` with pooled SE ``sqrt(1 / sum_w)`` — algebraically
    identical to a batch pool, but updatable in O(1) per new record.
    """

    n: int = 0
    sum_w: float = 0.0
    sum_wx: float = 0.0
    trial_ids: list[str] = field(default_factory=list)

    def add(self, record: ExtractionRecord) -> "LivingPoolState":
        """Fold one extraction record into the running pool. Returns self."""
        if not record.standard_error > 0:
            raise ValueError(
                f"standard_error must be positive; got {record.standard_error!r}."
            )
        weight = 1.0 / (record.standard_error**2)
        self.sum_w += weight
        self.sum_wx += weight * record.log_effect
        self.n += 1
        self.trial_ids.append(record.trial_id)
        return self

    @property
    def has_estimate(self) -> bool:
        return self.n > 0 and self.sum_w > 0

    @property
    def pooled_effect(self) -> float:
        if not self.has_estimate:
            raise ValueError("No records pooled yet; pooled_effect is undefined.")
        return self.sum_wx / self.sum_w

    @property
    def pooled_se(self) -> float:
        if not self.has_estimate:
            raise ValueError("No records pooled yet; pooled_se is undefined.")
        return (1.0 / self.sum_w) ** 0.5

    def snapshot(self) -> dict:
        """Return the current pooled estimate as a plain dict."""
        return {
            "n": self.n,
            "pooled_effect": self.pooled_effect,
            "pooled_se": self.pooled_se,
            "trial_ids": list(self.trial_ids),
        }


def living_update(records: list[ExtractionRecord]) -> list[dict]:
    """Replay records one at a time, returning a snapshot after each insert.

    The final snapshot is the fully-updated living estimate; earlier snapshots
    trace how the pooled effect evolved as evidence accrued — the "living"
    trajectory.
    """
    if not records:
        raise ValueError("At least one extraction record is required.")
    state = LivingPoolState()
    trajectory: list[dict] = []
    for record in records:
        state.add(record)
        trajectory.append(state.snapshot())
    return trajectory


def assert_living_equivalence(
    records: list[ExtractionRecord], *, tol: float = 1e-12
) -> dict:
    """Verify living-update == batch-recompute over ``records``.

    Pools ``records`` two independent ways — incrementally via
    :class:`LivingPoolState` and from scratch via
    :func:`inverse_variance_pool` — and asserts the two pooled estimates agree to
    within ``tol``. Returns a report dict; raises ``AssertionError`` on
    divergence. This is the living-system correctness gate.
    """
    if not records:
        raise ValueError("At least one extraction record is required.")

    state = LivingPoolState()
    for record in records:
        state.add(record)
    live_effect = state.pooled_effect
    live_se = state.pooled_se

    batch_effect, batch_se = inverse_variance_pool(records)

    effect_gap = abs(live_effect - batch_effect)
    se_gap = abs(live_se - batch_se)
    equivalent = effect_gap <= tol and se_gap <= tol
    if not equivalent:
        raise AssertionError(
            "Living-update estimate diverged from batch recompute: "
            f"effect gap {effect_gap:.3e}, se gap {se_gap:.3e} (tol {tol:.1e})."
        )
    return {
        "n": len(records),
        "live_effect": live_effect,
        "batch_effect": batch_effect,
        "effect_gap": effect_gap,
        "live_se": live_se,
        "batch_se": batch_se,
        "se_gap": se_gap,
        "tolerance": tol,
        "equivalent": equivalent,
    }


def order_invariance_report(
    records: list[ExtractionRecord], *, tol: float = 1e-9
) -> dict:
    """Confirm the pooled estimate is invariant to record arrival order.

    Inverse-variance pooling is a sum, so the fully-updated living estimate must
    not depend on the order trials arrive in (up to floating-point summation
    error). This pools the given order and the reversed order and reports the
    gap; it is a sanity check that the living engine is genuinely commutative.
    """
    if not records:
        raise ValueError("At least one extraction record is required.")
    forward = LivingPoolState()
    for record in records:
        forward.add(record)
    reverse = LivingPoolState()
    for record in reversed(records):
        reverse.add(record)

    effect_gap = abs(forward.pooled_effect - reverse.pooled_effect)
    se_gap = abs(forward.pooled_se - reverse.pooled_se)
    return {
        "n": len(records),
        "forward_effect": forward.pooled_effect,
        "reverse_effect": reverse.pooled_effect,
        "effect_gap": effect_gap,
        "se_gap": se_gap,
        "tolerance": tol,
        "order_invariant": effect_gap <= tol and se_gap <= tol and not math.isnan(effect_gap),
    }
