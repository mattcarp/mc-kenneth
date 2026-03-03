import unittest

from auto_tune import (
    RSPDX_R2_MAX_HZ,
    RSPDX_R2_MIN_HZ,
    SpectrumSample,
    build_scan_frequencies,
    clamp_to_rspdx_r2_limits,
    detect_active_frequencies,
    validate_scan_range,
)


class AutoTuneWidebandTest(unittest.TestCase):
    def test_clamp_to_rspdx_limits(self) -> None:
        self.assertEqual(clamp_to_rspdx_r2_limits(-1), RSPDX_R2_MIN_HZ)
        self.assertEqual(clamp_to_rspdx_r2_limits(100_000_000), 100_000_000)
        self.assertEqual(clamp_to_rspdx_r2_limits(RSPDX_R2_MAX_HZ + 1), RSPDX_R2_MAX_HZ)

    def test_validate_scan_range_rejects_non_positive_step(self) -> None:
        with self.assertRaises(ValueError):
            validate_scan_range(100_000_000, 101_000_000, 0)

    def test_validate_scan_range_rejects_invalid_order_after_clamping(self) -> None:
        with self.assertRaises(ValueError):
            validate_scan_range(RSPDX_R2_MAX_HZ + 1, RSPDX_R2_MIN_HZ - 1, 100_000)

    def test_build_scan_frequencies_uses_clamped_bounds(self) -> None:
        freqs = build_scan_frequencies(
            start_hz=RSPDX_R2_MIN_HZ - 1,
            stop_hz=RSPDX_R2_MIN_HZ + 300_000,
            step_hz=100_000,
        )
        self.assertEqual(freqs[0], RSPDX_R2_MIN_HZ)
        self.assertEqual(freqs, [RSPDX_R2_MIN_HZ, RSPDX_R2_MIN_HZ + 100_000, RSPDX_R2_MIN_HZ + 200_000, RSPDX_R2_MIN_HZ + 300_000])

    def test_detect_active_frequencies_uses_noise_floor_and_spacing(self) -> None:
        samples = [
            SpectrumSample(100_000_000, -60.0),
            SpectrumSample(100_100_000, -59.0),
            SpectrumSample(100_150_000, -61.0),
            SpectrumSample(100_200_000, -30.0),
            SpectrumSample(100_250_000, -29.0),
            SpectrumSample(100_300_000, -62.0),
            SpectrumSample(100_900_000, -28.0),
        ]
        active = detect_active_frequencies(samples, min_snr_db=10.0, min_spacing_hz=100_000, max_results=10)
        self.assertEqual([sample.frequency_hz for sample in active], [100_250_000, 100_900_000])

    def test_detect_active_frequencies_empty_input(self) -> None:
        self.assertEqual(detect_active_frequencies([]), [])


if __name__ == "__main__":
    unittest.main()
