# Efficient export pipeline benchmark

This report compares the protected per-segment route with adaptive grouped source preparation on the same generated mixed-source fixture. Each strategy has 3 repetition(s).

| Strategy | Status | Median wall (s) | Min (s) | Max (s) | Child CPU (s) | FFmpeg processes | Normalize processes | Interpolation calls | Boundary-safe | Source preserved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| per-segment | passed | 68.2237 | 68.175 | 68.3439 | 77.3358 | 11 | 3 | 2 | True | True |
| adaptive | passed | 67.8984 | 67.8779 | 68.0519 | 77.253 | 8 | 2 | 2 | True | True |

Selected strategy: `adaptive`.

Selected the fastest candidate that passed the technical integrity gates.

## Comparison

| Metric | Adaptive vs per-segment |
|---|---:|
| Wall-time change | 0.3253 seconds (0.48%) |
| FFmpeg process change | -3 |
| Normalization process change | -1 |
| Interpolation-call change | 0 |

## Stage timing

| Strategy | Stage | Median seconds |
|---|---|---:|
| per-segment | composing enhanced segments | 0.7451 |
| per-segment | concatenating enhanced segments | 0.0398 |
| per-segment | cut 1/1 | 0.0524 |
| per-segment | interpolation | 12.8759 |
| per-segment | interpolation segment 1/3 | 25.7872 |
| per-segment | interpolation segment 2/3 | 25.7501 |
| per-segment | normalizing source | 0.79 |
| adaptive | composing enhanced segments | 0.7518 |
| adaptive | concatenating enhanced segments | 0.0398 |
| adaptive | interpolation | 12.8606 |
| adaptive | interpolation segment 1/3 | 25.7916 |
| adaptive | interpolation segment 2/3 | 25.7287 |
| adaptive | normalizing source | 0.5225 |
| adaptive | normalizing source run | 0.208 |

The benchmark is hardware- and fixture-specific. It does not replace the target-workstation visual review or the resumability functionality tests. The operating-system file cache was not flushed between repetitions, and GPU values are point-in-time observations rather than averages.
