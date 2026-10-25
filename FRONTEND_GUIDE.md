# Optional Streamlit frontend

This dashboard is **additional** to the official submission. The required command remains `python checker.py PACK_DIR`, which writes `flags.csv` in the current working directory. The repository must not include the private dataset.

## Run it on a Mac

From the project root (with your `.venv` activated):

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Your browser should open at http://localhost:8501. The application suggests `~/Downloads/ridgeline_extracted` as the default dataset path; replace it in the sidebar if necessary, then click **Analyze dataset**.

## Pages

- Overview — station and issue counts.
- Station explorer — time-series graphs and overlapping episode flags.
- Issue flags — action/station/channel filters and exports.
- GPS & maintenance — NMEA diagnostics and volunteer notes.
- Technician & report — S06 visit recommendation for the **supplied dataset only**, plus the official printable HTML report.

## Caveats

- Chart markers and summaries are computed from the current pack; chart data may be downsampled for display only.
- `generate_report.py` contains **station-specific recommendations for the supplied assignment pack**. These are not valid for an arbitrary second pack without re-evaluation; the checker itself is the reusable part.
- Do not host this dashboard with the private data pack or upload it to GitHub.
- Do not confuse the number of flagged *episodes* with the number of affected records.
- The app does not overwrite source files or apply speculative corrections.
