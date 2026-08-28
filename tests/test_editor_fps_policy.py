import unittest
from fractions import Fraction

from resolve_editor.fps_policy import (
    FrameRatePolicyError,
    canonical_rate,
    resolve_frame_rate_policy,
    supports_interpolation,
)


def source(source_id: str, rate: str, *, variable: bool = False) -> dict[str, object]:
    return {
        "source_id": source_id,
        "frame_rate": rate,
        "variable_frame_rate": variable,
    }


class EditorFpsPolicyTests(unittest.TestCase):
    def test_resolves_lowest_highest_custom_and_sixty_choices_as_rationals(self):
        sources = (source("one", "30000/1001"), source("two", "60/1"))

        lowest = resolve_frame_rate_policy(sources, choice="lowest")
        highest = resolve_frame_rate_policy(sources, choice="highest")
        custom = resolve_frame_rate_policy(sources, choice="custom", custom_rate="59.94")
        sixty = resolve_frame_rate_policy(sources, choice="60")

        self.assertEqual(lowest.target_rate, Fraction(30000, 1001))
        self.assertEqual(highest.target_rate, Fraction(60, 1))
        self.assertEqual(custom.target_rate, Fraction(2997, 50))
        self.assertEqual(sixty.target_rate, Fraction(60, 1))
        self.assertEqual(custom.to_dict()["target_rate"], "2997/50")

    def test_default_policy_targets_sixty_with_enhancement_enabled(self):
        resolved = resolve_frame_rate_policy(
            (
                source("slow", "30000/1001"),
                source("target", "60/1"),
                source("fast", "120/1"),
            ),
        )

        self.assertEqual(resolved.policy.choice, "60")
        self.assertEqual(resolved.policy.target_rate, Fraction(60, 1))
        self.assertTrue(resolved.policy.enhancement_enabled)
        self.assertEqual(
            {item.source_id: item.action for item in resolved.decisions},
            {
                "slow": "interpolate",
                "target": "passthrough",
                "fast": "convert-down",
            },
        )
        self.assertFalse(resolved.has_unsupported_sources)

    def test_enabled_enhancement_only_interpolates_sources_below_target(self):
        resolved = resolve_frame_rate_policy(
            (
                source("slow", "30000/1001"),
                source("target", "60/1"),
                source("fast", "120/1"),
            ),
            choice="60",
            enhancement_enabled=True,
        )

        self.assertEqual(resolved.decisions[0].action, "interpolate")
        self.assertTrue(resolved.decisions[0].eligible)
        self.assertEqual(resolved.decisions[1].action, "passthrough")
        self.assertEqual(resolved.decisions[2].action, "convert-down")
        self.assertIn("above", resolved.decisions[2].reason.lower())

    def test_rve_rejects_vfr_but_uses_gpu_oversampling_for_fractional_rate(self):
        fractional = resolve_frame_rate_policy(
            (source("source", "24/1"),),
            choice="60",
            enhancement_enabled=True,
        )
        vfr = resolve_frame_rate_policy(
            (source("source", "30000/1001", variable=True),),
            choice="60",
            enhancement_enabled=True,
        )

        self.assertFalse(fractional.has_unsupported_sources)
        self.assertEqual(fractional.decisions[0].action, "interpolate")
        self.assertTrue(fractional.decisions[0].eligible)
        self.assertTrue(vfr.has_unsupported_sources)
        self.assertIn("variable", vfr.decisions[0].reason.lower())

    def test_rve_uses_gpu_oversampling_for_fractional_interpolation_factor(self):
        self.assertTrue(
            supports_interpolation(
                Fraction(24000, 1001),
                Fraction(60, 1),
                backend="rve-4.26",
            )
        )
        resolved = resolve_frame_rate_policy(
            (source("source", "24000/1001"),),
            choice="60",
            enhancement_enabled=True,
        )

        self.assertFalse(resolved.has_unsupported_sources)
        self.assertEqual(resolved.decisions[0].action, "interpolate")
        self.assertTrue(resolved.decisions[0].eligible)

    def test_invalid_custom_rate_is_rejected_without_a_fallback(self):
        with self.assertRaises(FrameRatePolicyError):
            resolve_frame_rate_policy(
                (source("source", "30/1"),),
                choice="custom",
                custom_rate="0",
            )

        with self.assertRaisesRegex(FrameRatePolicyError, "only valid"):
            resolve_frame_rate_policy(
                (source("source", "30/1"),),
                choice="highest",
                custom_rate="60/1",
            )

        with self.assertRaises(FrameRatePolicyError):
            resolve_frame_rate_policy(
                (source("source", "30/1"),),
                choice="not-a-choice",
            )

    def test_canonical_rate_accepts_decimal_and_fraction_forms(self):
        self.assertEqual(canonical_rate("29.97"), Fraction(2997, 100))
        self.assertEqual(canonical_rate(30), Fraction(30, 1))
        self.assertEqual(canonical_rate(Fraction(60000, 1001)), Fraction(60000, 1001))


if __name__ == "__main__":
    unittest.main()
