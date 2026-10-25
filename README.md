Garvit Kandpal
garvitjr47@gmail.com
[YOUR VIDEO LINK]
Run: python checker.py "/absolute/path/to/unzipped/data_pack"

# Ridgeline weather data quality checker

An explainable, read-only check of 10-minute weather observations and NMEA location/clock metadata. The CLI writes `flags.csv` into your **current working directory**; it reads any same-format pack and does not modify inputs.

## Optional visual interface

Run `python -m streamlit run app.py` after installing requirements. Enter the absolute path to the extracted pack, then click **Run quality analysis**. This frontend is optional and does not replace the required CLI output or printable A4 report.

See `GITHUB_UPLOAD_GUIDE.md` for an exact public-repository checklist.

## Setup and usage

```bash
python -m pip install -r requirements.txt
python checker.py "/absolute/path/to/unzipped/data_pack"
python generate_report.py "/absolute/path/to/unzipped/data_pack"
python -m pytest tests -q
```

Unzip your private data pack outside the public Git repo. The pack should have `stations.csv`, `data/`, and `gps/`; `maintenance_log.md` is consulted separately for human interpretation. Reports are printable on A4. Regenerate `flags.csv` whenever the source pack changes; do not use the included report for a different pack unless regenerated.

## Checks, assumptions, thresholds

- Schema, UTC parsing, station metadata, duplicate and missing ten-minute logger timestamps.
- Physical range checks: temperature −60…60 °C; humidity 0…100%; pressure 450…1100 hPa; wind 0…250 km/h; direction 0…360°; rain 0…250 mm per interval; irradiance 0…1500 W/m².
- At least 24 h of exactly equal temperature/RH/pressure/wind/irradiance = sensor persistence. Exact-zero rain is **not** considered a fault; nor is overnight zero irradiance.
- Temperature jumps >12 °C or pressure steps >4 hPa across exactly one sample interval are marked as exclusions; they are heuristics requiring inspection around both ends.
- Rain >8 mm per 10 minutes = `keep` (review; not automatically erroneous). Near-saturated sunny humidity can be flagged `keep` as a prompt for calibration review.
- NMEA `$GPRMC` and `$GPGGA`: valid fix, hemispheres/coordinates; coordinate disagreement >1 km from installation sheet; clock offsets >120 s. GPS errors are flagged under `metadata`, **not** as proof the weather itself is invalid.
- NMEA invalidity is grouped into GPS episodes. A `correct` action is deliberately not used: there is not enough independent evidence for a safe numerical correction.

**Known limitations:** No certified sensor calibration data, no independently verified rain gauge, wind anemometer transfer functions, altitude-aware peer network model, validated sun position model, or per-site learned climatology. The generic checker does not programmatically parse free-text maintenance notes; the report manually relates documented incidents. `report.html` contains site-specific narrative contextualization for this provided pack; the checker itself does not hardcode its incidents. A missing GPS file is reported with a metadata placeholder date and should be reviewed, not interpreted as real event timing. GPS NMEA checks do not validate XOR checksums. Flag rows denote episodes and can overlap where distinct rules identify the same suspicious region.

**Interpretation:** `exclude` means exclude that *channel's flagged interval* (or suspect metadata time), not the entire station. `keep` means further review / plausibly real, never a promise that it was verified. Rain evidence requires context.

## Submission checklist

- [ ] Edit first four lines of README with identity and video URL.
- [ ] Rewrite DECISIONS.md in your own words and independently validate S04 sun calculation.
- [ ] Export **complete** AI conversation to `ai_logs/`, including false starts (not a fabricated log).
- [ ] Record 3-minute **unedited** narrated screen walkthrough of original S03 flatline, S04 disputed rain and S06 clock/visit reasoning.
- [ ] Make genuine incremental Git commits, push public `firstname-lastname` repo. **Never commit data pack**.
- [ ] Fill out Aeron's submission form within 48 hours of when your invitation was sent.

## Git commands

```bash
git init
git add checker.py requirements.txt tests .gitignore
git commit -m "Implement core weather and NMEA checks"
git add flags.csv generate_report.py report.html README.md DECISIONS.md ai_logs
git commit -m "Add reviewed results and submission documentation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/firstname-lastname.git
git push -u origin main
```

Only run these when you have created and verified the corresponding files. Never imply AI chat logs or screen recording exist until you provide them.
