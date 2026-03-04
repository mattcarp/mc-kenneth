from unittest.mock import patch

import numpy as np

from rtl_sdr_real_capture import RTLSDRRealCapture


def _capture() -> RTLSDRRealCapture:
    with patch.object(RTLSDRRealCapture, "check_rtl_sdr", return_value=False):
        return RTLSDRRealCapture()


def test_select_demod_mode_uses_am_for_aviation_band() -> None:
    capture = _capture()
    assert capture._select_demod_mode(108.0) == "am"
    assert capture._select_demod_mode(121.5) == "am"
    assert capture._select_demod_mode(137.0) == "am"


def test_select_demod_mode_uses_nfm_for_maritime_band() -> None:
    capture = _capture()
    assert capture._select_demod_mode(156.8) == "nfm"


def test_am_demodulation_decimates_to_48khz() -> None:
    capture = _capture()
    sample_rate = 2_048_000
    count = sample_rate // 2
    t = np.arange(count, dtype=np.float32) / sample_rate

    carrier_hz = 60_000.0
    tone_hz = 1_000.0
    modulation = 1.0 + 0.5 * np.sin(2 * np.pi * tone_hz * t)
    iq = (modulation * np.exp(1j * 2 * np.pi * carrier_hz * t)).astype(np.complex64)

    audio = capture.am_demodulate(iq, sample_rate)

    assert audio is not None
    expected = int(round(count * 48_000 / sample_rate))
    assert abs(len(audio) - expected) <= 1
