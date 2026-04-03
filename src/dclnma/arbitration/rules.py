from __future__ import annotations

from dataclasses import dataclass

from ..data.models import DecisionCapsule, WitnessEstimate


@dataclass(slots=True)
class ArbitrationPolicy:
    disagreement_low: float = 0.05
    disagreement_high: float = 0.15
    mid_inflation: float = 1.3
    high_inflation: float = 2.0


def _determine_action(lower: float, upper: float, disagreement_level: str) -> str:
    if disagreement_level == "high":
        return "research"
    if upper < 0:
        return "recommend"
    if lower > 0:
        return "do_not_use"
    return "research"


def arbitrate_witnesses(
    witnesses: list[WitnessEstimate], policy: ArbitrationPolicy | None = None
) -> DecisionCapsule:
    if not witnesses:
        raise ValueError("At least one witness estimate is required.")

    policy = policy or ArbitrationPolicy()
    effects = [w.effect for w in witnesses]
    center = sum(effects) / len(effects)
    disagreement = max(abs(effect - center) for effect in effects)

    if disagreement <= policy.disagreement_low:
        disagreement_level = "low"
        inflation = 1.0
    elif disagreement <= policy.disagreement_high:
        disagreement_level = "mid"
        inflation = policy.mid_inflation
    else:
        disagreement_level = "high"
        inflation = policy.high_inflation

    half_width = 0.0
    for witness in witnesses:
        witness_center = (witness.lower + witness.upper) / 2
        witness_half_width = (witness.upper - witness.lower) / 2
        candidate = abs(witness_center - center) + witness_half_width
        half_width = max(half_width, candidate)

    lower = center - inflation * half_width
    upper = center + inflation * half_width
    action = _determine_action(lower, upper, disagreement_level)
    reversal_risk = min(1.0, disagreement + (inflation - 1.0) * 0.25)
    regret = 0.5 if action == "research" else 0.0

    integrity_profile = {
        "witness_count": len(witnesses),
        "disagreement": disagreement,
        "inflation": inflation,
    }
    return DecisionCapsule(
        effect=center,
        lower=lower,
        upper=upper,
        disagreement_level=disagreement_level,
        recommended_action=action,
        reversal_risk=reversal_risk,
        decision_regret=regret,
        witnesses=witnesses,
        evidence_integrity_profile=integrity_profile,
    )
