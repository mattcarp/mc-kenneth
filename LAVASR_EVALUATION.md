# LavaSR v2 Evaluation

Generated: 2026-03-02 00:58:59 UTC

## Summary

- LavaSR v2 processing did not complete in this environment.
- Input source: `synthetic`
- Input file: `/home/sysop/projects/mc-kenneth/lavasr_eval_output/synthetic_input.wav`
- Output file: `/home/sysop/projects/mc-kenneth/lavasr_eval_output/lavasr_v2_output.wav`

## Installation Notes

```text
Attempted install commands:
1) python3 -m pip install lavasr
   -> failed with PEP 668 (externally-managed-environment).
2) python3 -m venv .venv && .venv/bin/pip install lavasr
   -> failed: DNS resolution error to package index and 'No matching distribution found for lavasr'.
```

## LavaSR Execution

Status: **LavaSR invocation failed**

```text
$ /usr/bin/python3 -m lavasr --input /home/sysop/projects/mc-kenneth/lavasr_eval_output/synthetic_input.wav --output /home/sysop/projects/mc-kenneth/lavasr_eval_output/lavasr_v2_output.wav --model v2\nexit=1\nstdout=<empty>\nstderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr -i /home/sysop/projects/mc-kenneth/lavasr_eval_output/synthetic_input.wav -o /home/sysop/projects/mc-kenneth/lavasr_eval_output/lavasr_v2_output.wav --model v2\nexit=1\nstdout=<empty>\nstderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr /home/sysop/projects/mc-kenneth/lavasr_eval_output/synthetic_input.wav /home/sysop/projects/mc-kenneth/lavasr_eval_output/lavasr_v2_output.wav --model v2\nexit=1\nstdout=<empty>\nstderr=/usr/bin/python3: No module named lavasr
```

## Before/After Metrics

| Metric | Before | After |
|---|---:|---:|
| File size (bytes) | 96044 | 0 |
| Sample rate (Hz) | 16000 | n/a |
| Basic SNR estimate (dB) | n/a | n/a |

## Findings

- `pip install lavasr` failed due environment/package-index constraints, so LavaSR v2 could not be executed here.
- Script generated a synthetic WAV fallback input and still recorded baseline metrics and failure logs.
- Re-run in an environment with PyPI access and a resolvable `lavasr` package to complete a true before/after benchmark.
