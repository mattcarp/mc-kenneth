#!/usr/bin/env python3
"""Wideband spectrum scan for SDRplay RSPdx-R2 active-frequency detection."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np

RSPDX_R2_MIN_HZ = 10_000
RSPDX_R2_MAX_HZ = 2_000_000_000


@dataclass(frozen=True)
class SpectrumSample:
    """Single frequency-power sample."""

    frequency_hz: int
    power_dbfs: float


def clamp_to_rspdx_r2_limits(frequency_hz: int) -> int:
    """Clamp a frequency to RSPdx-R2 supported limits."""
    return max(RSPDX_R2_MIN_HZ, min(RSPDX_R2_MAX_HZ, int(frequency_hz)))


def validate_scan_range(start_hz: int, stop_hz: int, step_hz: int) -> tuple[int, int, int]:
    """Validate and normalize scan range to RSPdx-R2 limits."""
    if step_hz <= 0:
        raise ValueError("step_hz must be greater than zero")

    clamped_start = clamp_to_rspdx_r2_limits(start_hz)
    clamped_stop = clamp_to_rspdx_r2_limits(stop_hz)

    if clamped_start > clamped_stop:
        raise ValueError("start_hz must be <= stop_hz after clamping to RSPdx-R2 limits")

    return clamped_start, clamped_stop, int(step_hz)


def build_scan_frequencies(start_hz: int, stop_hz: int, step_hz: int) -> List[int]:
    """Build evenly stepped scan frequencies."""
    validated_start, validated_stop, validated_step = validate_scan_range(start_hz, stop_hz, step_hz)
    return list(range(validated_start, validated_stop + 1, validated_step))


def detect_active_frequencies(
    samples: Sequence[SpectrumSample],
    min_snr_db: float = 8.0,
    min_spacing_hz: int = 100_000,
    max_results: int = 20,
) -> List[SpectrumSample]:
    """Auto-detect active frequencies from sampled power points."""
    if not samples:
        return []

    powers = np.array([sample.power_dbfs for sample in samples], dtype=np.float64)
    noise_floor = float(np.median(powers))
    threshold = noise_floor + min_snr_db
    candidates = [sample for sample in samples if sample.power_dbfs >= threshold]
    candidates.sort(key=lambda sample: sample.power_dbfs, reverse=True)

    selected: List[SpectrumSample] = []
    for candidate in candidates:
        too_close = any(abs(candidate.frequency_hz - kept.frequency_hz) < min_spacing_hz for kept in selected)
        if too_close:
            continue
        selected.append(candidate)
        if len(selected) >= max_results:
            break

    return sorted(selected, key=lambda sample: sample.frequency_hz)


def _mean_power_dbfs(iq_samples: np.ndarray) -> float:
    """Compute relative dBFS estimate from complex IQ samples."""
    if iq_samples.size == 0:
        return -200.0
    power = float(np.mean(np.abs(iq_samples) ** 2))
    return 10.0 * math.log10(power + 1e-20)


def scan_wideband_rspdx_r2(
    start_hz: int,
    stop_hz: int,
    step_hz: int,
    sample_rate_hz: int = 2_000_000,
    gain_db: float = 40.0,
    dwell_seconds: float = 0.08,
) -> List[SpectrumSample]:
    """Run wideband scan using SoapySDR with SDRplay driver."""
    try:
        import SoapySDR  # pylint: disable=import-error
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "SoapySDR Python module is required for RSPdx-R2 wideband scan"
        ) from exc

    frequencies = build_scan_frequencies(start_hz, stop_hz, step_hz)
    if not frequencies:
        return []

    sdr = SoapySDR.Device({"driver": "sdrplay"})
    sdr.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, float(sample_rate_hz))
    sdr.setGain(SoapySDR.SOAPY_SDR_RX, 0, float(gain_db))

    rx_stream = sdr.setupStream(SoapySDR.SOAPY_SDR_RX, SoapySDR.SOAPY_SDR_CF32)
    sdr.activateStream(rx_stream)

    samples_per_freq = max(1024, int(sample_rate_hz * dwell_seconds))
    chunk_size = min(32_768, samples_per_freq)
    points: List[SpectrumSample] = []

    try:
        for frequency_hz in frequencies:
            sdr.setFrequency(SoapySDR.SOAPY_SDR_RX, 0, float(frequency_hz))
            captured = np.zeros(0, dtype=np.complex64)

            while captured.size < samples_per_freq:
                buffer = np.zeros(chunk_size, dtype=np.complex64)
                result = sdr.readStream(rx_stream, [buffer], chunk_size, timeoutUs=200_000)
                if result.ret <= 0:
                    continue
                captured = np.concatenate((captured, buffer[: result.ret]))

            power_dbfs = _mean_power_dbfs(captured[:samples_per_freq])
            points.append(SpectrumSample(frequency_hz=frequency_hz, power_dbfs=power_dbfs))
    finally:
        sdr.deactivateStream(rx_stream)
        sdr.closeStream(rx_stream)

    return points


def _format_hz(frequency_hz: int) -> str:
    return f"{frequency_hz / 1e6:.6f} MHz"


def _print_scan_report(samples: Iterable[SpectrumSample], active: Sequence[SpectrumSample]) -> None:
    sample_list = list(samples)
    print("=" * 64)
    print("Wideband Spectrum Scan (RSPdx-R2)")
    print("=" * 64)
    print(f"Sample points: {len(sample_list)}")
    if not sample_list:
        print("No samples captured.")
        return

    powers = [sample.power_dbfs for sample in sample_list]
    print(f"Power range: {min(powers):.2f} dBFS to {max(powers):.2f} dBFS")
    print("-" * 64)

    if not active:
        print("No active frequencies detected above threshold.")
        return

    print("Detected active frequencies:")
    for sample in active:
        print(f"  {_format_hz(sample.frequency_hz):>14}  {sample.power_dbfs:8.2f} dBFS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-detect active frequencies with wideband RSPdx-R2 spectrum scan."
    )
    parser.add_argument("--start-hz", type=int, default=88_000_000, help="Start frequency in Hz.")
    parser.add_argument("--stop-hz", type=int, default=108_000_000, help="Stop frequency in Hz.")
    parser.add_argument("--step-hz", type=int, default=200_000, help="Frequency step in Hz.")
    parser.add_argument("--sample-rate-hz", type=int, default=2_000_000, help="Sample rate in Hz.")
    parser.add_argument("--gain-db", type=float, default=40.0, help="Receiver gain in dB.")
    parser.add_argument("--dwell-seconds", type=float, default=0.08, help="Capture dwell per step in seconds.")
    parser.add_argument("--min-snr-db", type=float, default=8.0, help="SNR above median noise floor.")
    parser.add_argument("--min-spacing-hz", type=int, default=100_000, help="Minimum spacing between active hits.")
    parser.add_argument("--max-results", type=int, default=20, help="Max active frequencies to report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start_hz, stop_hz, step_hz = validate_scan_range(args.start_hz, args.stop_hz, args.step_hz)

    try:
        samples = scan_wideband_rspdx_r2(
            start_hz=start_hz,
            stop_hz=stop_hz,
            step_hz=step_hz,
            sample_rate_hz=args.sample_rate_hz,
            gain_db=args.gain_db,
            dwell_seconds=args.dwell_seconds,
        )
    except RuntimeError as exc:
        print(f"Scan failed: {exc}")
        return 2

    active = detect_active_frequencies(
        samples=samples,
        min_snr_db=args.min_snr_db,
        min_spacing_hz=args.min_spacing_hz,
        max_results=args.max_results,
    )
    _print_scan_report(samples, active)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
