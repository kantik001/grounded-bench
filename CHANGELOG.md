# Changelog

## [0.1.0] - 2026-07-28

### Added

- Offline benchmark track with **NVR / CP / HR / RR**
- Deterministic dataset generator (`dataset/generate_v0.py`, seed `42`, 280 cases)
- Bundled `predictions/oracle.jsonl` and `predictions/weak-baseline.jsonl`
- CLI: `grounded-bench validate|run|publish`
- Static leaderboard under `leaderboard/`
- CI (pytest + validate + oracle quality gate)
