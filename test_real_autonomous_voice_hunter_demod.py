from pathlib import Path

import numpy as np

from real_autonomous_voice_hunter import RealAutonomousVoiceHunter


def _hunter(tmp_path: Path) -> RealAutonomousVoiceHunter:
    return RealAutonomousVoiceHunter(session_name=f"test_demod_{tmp_path.name}")


def test_select_demod_mode_uses_am_for_malta_approach_119_45mhz(tmp_path: Path) -> None:
    hunter = _hunter(tmp_path)
    assert hunter._select_demod_mode(119.45e6) == "am"


def test_select_demod_mode_uses_nfm_for_maritime_band(tmp_path: Path) -> None:
    hunter = _hunter(tmp_path)
    assert hunter._select_demod_mode(156.8e6) == "nfm"


def test_demod_outputs_are_resampled_to_16khz(tmp_path: Path) -> None:
    hunter = _hunter(tmp_path)
    iq = np.exp(1j * np.linspace(0.0, 8.0 * np.pi, 200000)).astype(np.complex64)

    am_audio = hunter._am_demodulate(iq)
    nfm_audio = hunter._nfm_demodulate(iq)
    fm_audio = hunter._fm_demodulate(iq)

    expected = int(round(len(iq) * hunter.demod_audio_sample_rate / hunter.sample_rate))
    assert abs(len(am_audio) - expected) <= 1
    assert abs(len(nfm_audio) - expected) <= 1
    assert abs(len(fm_audio) - expected) <= 1
