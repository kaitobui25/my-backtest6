# Changelog

## v0.2.0 — 2026-07-12

- Added 15 converted indicator strategy plugins from the supplied source files.
- Added cached indicator library and compact precomputed-signal adapter.
- Added shared YAML execution anchor for ATR stop, RR, max hold, and side.
- Enabled 17 total strategy families in the default config.
- Added `count_configs.bat`; default grid contains 23,796 exact configs.
- Reused identical compiled stateless kernels across strategy families.
- Added strategy-library, mapping, and simple/stateful extension documentation.
- Added smoke and signal-cache tests; 10 tests pass.
