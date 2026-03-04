import unittest

from auto_tune import (
    DEFAULT_WIDEBAND_START_HZ,
    DEFAULT_WIDEBAND_STOP_HZ,
    SpectrumSample,
    detect_wideband_active_frequencies,
)


class WidebandServiceTest(unittest.TestCase):
    def test_detect_wideband_active_frequencies_uses_default_80_to_500mhz_and_logs(self) -> None:
        calls = {}

        def fake_scan(start_hz, stop_hz, step_hz, sample_rate_hz, gain_db, dwell_seconds):
            calls["args"] = {
                "start_hz": start_hz,
                "stop_hz": stop_hz,
                "step_hz": step_hz,
                "sample_rate_hz": sample_rate_hz,
                "gain_db": gain_db,
                "dwell_seconds": dwell_seconds,
            }
            return [
                SpectrumSample(156_800_000, -34.0),
                SpectrumSample(157_100_000, -33.0),
                SpectrumSample(300_000_000, -67.0),
            ]

        with self.assertLogs("auto_tune", level="INFO") as log_context:
            active = detect_wideband_active_frequencies(scan_fn=fake_scan, min_snr_db=0.5)

        self.assertEqual(calls["args"]["start_hz"], DEFAULT_WIDEBAND_START_HZ)
        self.assertEqual(calls["args"]["stop_hz"], DEFAULT_WIDEBAND_STOP_HZ)
        self.assertEqual([sample.frequency_hz for sample in active], [157_100_000])
        self.assertTrue(any("Active frequency detected" in line for line in log_context.output))

    def test_detect_wideband_active_frequencies_clamps_when_requested_range_exceeds_hw_limit(self) -> None:
        calls = {}

        def fake_scan(start_hz, stop_hz, step_hz, sample_rate_hz, gain_db, dwell_seconds):
            calls["start_hz"] = start_hz
            calls["stop_hz"] = stop_hz
            return []

        detect_wideband_active_frequencies(
            start_hz=1,
            stop_hz=3_000_000_000,
            scan_fn=fake_scan,
        )

        self.assertEqual(calls["start_hz"], 10_000)
        self.assertEqual(calls["stop_hz"], 2_000_000_000)


if __name__ == "__main__":
    unittest.main()
