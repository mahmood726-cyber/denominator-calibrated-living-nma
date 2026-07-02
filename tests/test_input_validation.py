from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dclnma.data.linkage import inverse_variance_pool
from dclnma.data.models import ExtractionRecord, Provenance


def _extraction(standard_error: float, log_effect: float = -0.1) -> ExtractionRecord:
    return ExtractionRecord(
        extraction_id="e",
        publication_id="p",
        trial_id="t",
        endpoint_key="k",
        effect_measure="HR",
        reported_effect=0.9,
        reported_ci_lower=0.8,
        reported_ci_upper=1.0,
        log_effect=log_effect,
        log_ci_lower=log_effect - 0.2,
        log_ci_upper=log_effect + 0.2,
        standard_error=standard_error,
        provenance=Provenance(source_id="s", source_type="pdf", locator="l", confidence=0.9),
    )


class InverseVariancePoolValidationTests(unittest.TestCase):
    def test_empty_input_raises(self) -> None:
        with self.assertRaises(ValueError):
            inverse_variance_pool([])

    def test_zero_standard_error_raises_valueerror_not_zerodivision(self) -> None:
        with self.assertRaises(ValueError):
            inverse_variance_pool([_extraction(0.0)])

    def test_negative_standard_error_raises(self) -> None:
        # Previously silently accepted: se ** 2 keeps the weight positive and
        # produced a wrong pooled SE instead of an error.
        with self.assertRaises(ValueError):
            inverse_variance_pool([_extraction(-0.1)])

    def test_valid_single_record_pools_to_itself(self) -> None:
        pooled, pooled_se = inverse_variance_pool([_extraction(0.1, log_effect=-0.12)])
        self.assertAlmostEqual(pooled, -0.12)
        self.assertAlmostEqual(pooled_se, 0.1)

    def test_valid_equal_weight_pool(self) -> None:
        pooled, pooled_se = inverse_variance_pool(
            [_extraction(0.1, log_effect=-0.20), _extraction(0.1, log_effect=-0.10)]
        )
        self.assertAlmostEqual(pooled, -0.15)
        # Two equal-precision studies halve the variance: se = 0.1 / sqrt(2).
        self.assertAlmostEqual(pooled_se, 0.1 / (2 ** 0.5))


if __name__ == "__main__":
    unittest.main()
