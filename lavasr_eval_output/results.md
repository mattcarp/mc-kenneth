# LavaSR v2 Ablation Results

Generated: 2026-03-02 01:06:00 UTC

## Summary

- Samples evaluated: **4**
- Samples with LavaSR output: **0**
- Samples with reference transcripts for WER: **0**
- Average WER before: **None**
- Average WER after: **None**
- Average WER delta (after-before): **None**
- Average PESQ delta (after-before): **None**
- Average STOI delta (after-before): **None**
- Integration recommendation: **no**

## Per-sample Results

| Sample | LavaSR | WER before | WER after | PESQ before | PESQ after | STOI before | STOI after |
|---|---|---:|---:|---:|---:|---:|---:|
| `audio_samples/net_fm_after.mp3` | False | None | None | None | None | None | None |
| `audio_samples/one_radio_after.mp3` | False | None | None | None | None | None | None |
| `audio_samples/one_radio_before.mp3` | False | None | None | None | None | None | None |
| `audio_samples/radio_malta_after.mp3` | False | None | None | None | None | None | None |

## Notes

- WER is computed from faster-whisper transcripts.
- When explicit ground-truth text is unavailable, a paired cleaner sample transcript is used as proxy reference.
- PESQ/STOI are included only when `pesq` and/or `pystoi` are installed.

## LavaSR Invocation Logs

```text
[net_fm_after.mp3]
$ /usr/bin/python3 -m lavasr --input /home/sysop/projects/mc-kenneth/audio_samples/net_fm_after.mp3 --output /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/net_fm_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr -i /home/sysop/projects/mc-kenneth/audio_samples/net_fm_after.mp3 -o /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/net_fm_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr /home/sysop/projects/mc-kenneth/audio_samples/net_fm_after.mp3 /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/net_fm_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

[one_radio_after.mp3]
$ /usr/bin/python3 -m lavasr --input /home/sysop/projects/mc-kenneth/audio_samples/one_radio_after.mp3 --output /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/one_radio_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr -i /home/sysop/projects/mc-kenneth/audio_samples/one_radio_after.mp3 -o /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/one_radio_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr /home/sysop/projects/mc-kenneth/audio_samples/one_radio_after.mp3 /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/one_radio_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

[one_radio_before.mp3]
$ /usr/bin/python3 -m lavasr --input /home/sysop/projects/mc-kenneth/audio_samples/one_radio_before.mp3 --output /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/one_radio_before__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr -i /home/sysop/projects/mc-kenneth/audio_samples/one_radio_before.mp3 -o /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/one_radio_before__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr /home/sysop/projects/mc-kenneth/audio_samples/one_radio_before.mp3 /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/one_radio_before__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

[radio_malta_after.mp3]
$ /usr/bin/python3 -m lavasr --input /home/sysop/projects/mc-kenneth/audio_samples/radio_malta_after.mp3 --output /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/radio_malta_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr -i /home/sysop/projects/mc-kenneth/audio_samples/radio_malta_after.mp3 -o /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/radio_malta_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr

$ /usr/bin/python3 -m lavasr /home/sysop/projects/mc-kenneth/audio_samples/radio_malta_after.mp3 /home/sysop/projects/mc-kenneth/lavasr_eval_output/enhanced/radio_malta_after__lavasr_v2.wav --model v2
exit=1
stdout=<empty>
stderr=/usr/bin/python3: No module named lavasr
```
