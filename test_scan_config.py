import unittest

from scan_config import load_scan_config


class ScanConfigTest(unittest.TestCase):
    def test_scan_config_loads_and_contains_requested_bands(self) -> None:
        cfg = load_scan_config()
        entries = cfg["bands"]

        lookup = {
            (entry["name"], round(entry["frequency_mhz"], 3)): entry for entry in entries
        }

        required = [
            ("EPIRB 406", 406.028, "fm"),
            ("AIS 1", 161.975, "fm"),
            ("AIS 2", 162.025, "fm"),
            ("Marine CH16", 156.800, "nfm"),
            ("Marine CH09", 156.450, "nfm"),
            ("Marine CH13", 156.650, "nfm"),
            ("Marine CH22A", 157.100, "nfm"),
            ("Amateur 2m", 144.800, "nfm"),
            ("Amateur 70cm", 433.500, "nfm"),
        ]

        for name, freq_mhz, mode in required:
            key = (name, round(freq_mhz, 3))
            self.assertIn(key, lookup, f"missing band: {name} @ {freq_mhz} MHz")
            self.assertEqual(lookup[key]["demod_mode"], mode)


if __name__ == "__main__":
    unittest.main()
