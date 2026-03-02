# LavaSR v2 Ablation Results

Generated: 2026-03-02 02:04:02 UTC

## Setup

- Test inputs: synthetic voice-like audio, downsampled to 8 kHz and 16 kHz
- Target output: 48 kHz
- Baseline: linear interpolation upsample
- Metrics: SNR (dB, higher is better), LSD (dB, lower is better)
- LavaSR status: unavailable

## Results

| Case | Input SR | LavaSR ran | SNR before | SNR after | LSD before | LSD after |
|---|---:|---|---:|---:|---:|---:|
| synthetic_voice | 8000 | False | 23.341 | N/A | 26.062 | N/A |
| synthetic_voice | 16000 | False | 24.454 | N/A | 20.556 | N/A |

## Aggregate

- Average SNR before: 23.897 dB
- Average SNR after: N/A dB
- Average SNR delta: N/A dB
- Average LSD before: 23.309 dB
- Average LSD after: N/A dB
- Average LSD delta: N/A dB

## Notes

- LavaSR install/runtime is blocked in this environment; CLI calls failed for all tested invocation patterns.
- For production enhancement workloads, GPU inference is recommended; CPU-only runs can be too slow for real-time or batch throughput targets.
- Install command attempted: `pip install "torch>=2.2" lavasr`.

### LavaSR error logs

#### synthetic_voice @ 8000 Hz

```text
cmd=/usr/bin/python3 -m lavasr --input /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_8000hz_input.wav --output /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_8000hz_lavasr48k.wav --model v2 | exit=1 | stdout=<empty> | stderr=/usr/bin/python3: No module named lavasr
cmd=/usr/bin/python3 -m lavasr -i /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_8000hz_input.wav -o /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_8000hz_lavasr48k.wav --model v2 | exit=1 | stdout=<empty> | stderr=/usr/bin/python3: No module named lavasr
cmd=/usr/bin/python3 -m lavasr /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_8000hz_input.wav /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_8000hz_lavasr48k.wav --model v2 | exit=1 | stdout=<empty> | stderr=/usr/bin/python3: No module named lavasr
```

#### synthetic_voice @ 16000 Hz

```text
cmd=/usr/bin/python3 -m lavasr --input /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_16000hz_input.wav --output /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_16000hz_lavasr48k.wav --model v2 | exit=1 | stdout=<empty> | stderr=/usr/bin/python3: No module named lavasr
cmd=/usr/bin/python3 -m lavasr -i /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_16000hz_input.wav -o /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_16000hz_lavasr48k.wav --model v2 | exit=1 | stdout=<empty> | stderr=/usr/bin/python3: No module named lavasr
cmd=/usr/bin/python3 -m lavasr /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_16000hz_input.wav /home/sysop/projects/mc-kenneth/lavasr_ablation_output/audio/synthetic_voice_16000hz_lavasr48k.wav --model v2 | exit=1 | stdout=<empty> | stderr=/usr/bin/python3: No module named lavasr
```
