import unittest
from unittest.mock import patch

from auto_tune import SpectrumSample
from voice_hunting_scanner import VoiceHuntingScanner


class VoiceHuntingWidebandIntegrationTest(unittest.TestCase):
    def test_voice_hunting_scanner_includes_wideband_discoveries_in_maritime_frequencies(self) -> None:
        scanner = VoiceHuntingScanner()
        discovered = [
            SpectrumSample(156_800_000, -30.0),  # existing CH16
            SpectrumSample(160_300_000, -28.0),  # new
        ]

        scanner.integrate_discovered_frequencies(discovered)

        self.assertIn("AUTO 160.300 MHz", scanner.maritime_frequencies)
        self.assertEqual(scanner.maritime_frequencies["AUTO 160.300 MHz"], 160_300_000)

    def test_voice_hunting_scanner_runs_wideband_discovery_before_hunt(self) -> None:
        scanner = VoiceHuntingScanner()
        events = []

        def fake_discovery():
            events.append("discover")
            return [SpectrumSample(160_300_000, -28.0)]

        def fake_scan_frequency(name, frequency):
            events.append(("scan", name))
            return False, None

        with patch.object(scanner, "discover_wideband_activity", side_effect=fake_discovery):
            with patch.object(scanner, "scan_frequency", side_effect=fake_scan_frequency):
                with patch.object(scanner, "process_voice_sample", return_value=None):
                    with patch("voice_hunting_scanner.time.sleep", return_value=None):
                        scanner.hunt_for_voices()

        self.assertEqual(events[0], "discover")
        scan_events = [event for event in events if isinstance(event, tuple) and event[0] == "scan"]
        self.assertTrue(any(name == "AUTO 160.300 MHz" for _, name in scan_events))


if __name__ == "__main__":
    unittest.main()
