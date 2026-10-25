# Executed validation — 24 October 2026

- Actual data pack: eight station CSV files, installation metadata, GPS NMEA logs and volunteer maintenance notes inspected.
- `python checker.py /mnt/data/aeron_workspace/data_pack`: **success**, **200** issue episodes written to `flags.csv`.
- `python -m pytest tests -q`: **13 passed**.
- Running `python /mnt/data/aeron_submission/checker.py /mnt/data/aeron_workspace/data_pack` from a separate current directory produced a `flags.csv` **byte-for-byte identical** to the repository copy (`cmp` succeeded).
- HTML printed with WeasyPrint to PDF: **one A4 page**, 595.28 × 841.89 pt, visually inspected.
- Input ZIP and its unpacked weather data are **not** included in the project ZIP.
- Manual next steps: inspect source evidence with the user; manually validate the solar-noon exercise; add genuine full AI chat exports, real narration URL and identity; create incremental Git commits; submit before personal deadline.

## Engineering caveats

The generic checker is reusable, but the coordinator report includes fixed station-specific narrative based on this pack; re-check narrative if used on another pack. NMEA checksum verification, scientific cross-station comparisons, complete maintenance-log parsing and station-specific calibration are out of scope. Flags are evidence-informed heuristics, not certified quality assurance. The checker currently labels GPS void/malformed fixes as `exclude` under `metadata`; this does not mean the coincident weather must be dropped. Some episodes overlap because range and jump rules can describe the same anomaly from distinct perspectives.
