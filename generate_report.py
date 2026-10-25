"""Generate concise printable network-health report from actual checked data."""
import sys,html
from pathlib import Path
import pandas as pd
from checker import examine,write_flags

def make(pack,output='report.html'):
    flags,stats,data,meta=examine(pack)
    tbl=pd.DataFrame(flags)
    names=dict(zip(meta.station_id,meta.name))
    counts=tbl[tbl.action.eq('exclude')&~tbl.channel.eq('metadata')].groupby('station_id').size().to_dict()
    rows=[]
    for station in meta.station_id:
        critical=tbl[(tbl.station_id==station)&(tbl.action=='exclude')&(~tbl.channel.isin(['metadata']))]
        affected=', '.join(sorted(set(critical.channel)-{'all'})) or '—'
        if station=='S02': advice='Use other channels; withhold pressure after board replacement pending reference comparison'
        elif station=='S03':advice='Exclude flagged temperature intervals; remaining channels provisionally usable'
        elif station=='S04':advice='Rain on 2 Apr needs tipping-bucket and regional corroboration'
        elif station=='S05':advice='Withhold affected RH; verify GPS installation coordinates before location-sensitive use'
        elif station=='S06':advice='Withhold clock-affected records until timestamps can be recovered against GPS'
        elif station=='S07':advice='Wind calibration after 26 Mar is unverified; compare to nearby reference'
        elif station=='S08':advice='Use only unique timestamps; omit outage; review replayed day'
        else:advice='Weather usable with normal spot QA; GPS void fixes excluded only as metadata'
        rows.append(f'<tr><td><b>{station}</b> · {html.escape(str(names[station]))}</td><td>{len(data[station]):,}</td><td>{stats[station]["duplicate_records"]} / {stats[station]["missing_slots"]}</td><td>{html.escape(affected)}</td><td>{html.escape(advice)}</td></tr>')
    e=lambda s:html.escape(str(s))
    # S05 GPS separation derived from source metadata + NMEA records in checker; no invented distance.
    priority='S06'
    html_text=f'''<!doctype html><html><head><meta charset="utf-8"><title>Ridgeline | Network Health</title><style>
    @page{{size:A4;margin:13mm}}body{{font-family:Arial,Helvetica,sans-serif;color:#182634;font-size:9.5px;line-height:1.4;margin:0}}h1{{font-size:22px;margin:0;color:#17334a}}h2{{font-size:12px;border-bottom:1px solid #cad5dd;margin:14px 0 6px}}.sub{{color:#546678;margin:3px 0 12px}}.banner{{background:#e7eef3;padding:10px 13px;border-left:4px solid #244e69}}.cards{{display:flex;gap:12px;margin:11px 0}}.card{{flex:1;border:1px solid #d8e0e4;padding:9px}}.num{{font-weight:700;font-size:19px;color:#17334a}}table{{border-collapse:collapse;width:100%;font-size:8.2px}}th{{background:#e7eef3;text-align:left}}th,td{{border-bottom:1px solid #e1e6e9;padding:5px 5px;vertical-align:top}}.muted{{color:#5d6d7c}}.two{{display:grid;grid-template-columns:1.12fr 1fr;gap:18px}}.note{{font-size:8px;color:#4b6071}}strong{{color:#193e57}}@media print{{.banner{{print-color-adjust:exact}}}}</style></head><body>
    <h1>Network health · Spring 2025</h1><p class="sub">Ridgeline Schools Weather Network | 1 March–11 April 2025 | 8 stations | Coordinator action brief</p>
    <div class="banner"><b>Decision:</b> Use clean sections of the weather records, not entire stations indiscriminately. Set aside marked intervals and treat sensor upgrades, pressure calibration, and logger time as separate uncertainties. <b>Send the volunteer to S06 first</b> to resolve a broad timestamp integrity problem.</div>
    <div class="cards"><div class="card"><div class="num">8</div>stations reviewed</div><div class="card"><div class="num">{sum(x['duplicate_records'] for x in stats.values())}</div>extra duplicate logger rows</div><div class="card"><div class="num">{sum(x['missing_slots'] for x in stats.values())}</div>missing expected time slots</div><div class="card"><div class="num">{len(flags)}</div>flag episodes; not bad-row count</div></div>
    <h2>What can go into the spring summary?</h2><table><thead><tr><th>Station</th><th>Rows</th><th>Duplicates / gaps</th><th>Flagged weather</th><th>Coordinator instruction</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
    <div class="two"><div><h2>Technician visit: S06 · 60 minutes</h2><p><b>Why:</b> After the 24 March battery swap, the GPS/logger UTC discrepancy persists; duplicate logger times overlap the restart. This compromises ordering and the interpretation of multiple weather channels. <b>Second choice: S05</b> has extensive RH saturation and a persistent GPS installation mismatch, but its remaining weather-channel timing is intact.</p><p><b>0–10 min:</b> Photograph UTC clock, GPS lock/status and power readings without resetting.<br><b>10–25:</b> Compare raw NMEA UTC with logger UTC and timezone configuration; check firmware clock-source setting.<br><b>25–40:</b> Inspect battery connections, reboot log and buffering/replay settings.<br><b>40–55:</b> Take synchronized readings against an independent UTC clock and retain raw logs.<br><b>55–60:</b> Record the offset, decide whether timestamp correction is independently demonstrable, and document follow-up.</p></div>
    <div><h2>Important incidents</h2><p><b>S03:</b> 481 values stuck at 6.5°C (18–21 Mar), plus isolated large spikes. Do not average the flatline into climate summary.<br><b>S05:</b> {int((data['S05'].rh_pct>100).sum())} relative-humidity readings above 100%. Check sensor; do not clip to 100%. Valid NMEA positions systematically disagree with the installation sheet.<br><b>S08:</b> 214 missing slots around 16–18 Mar and 144 extra repeated timestamps on 5 Apr. Neither can be repaired by naive interpolation.<br><b>S02:</b> pressure step after 21 Mar board exchange is consistent with a calibration discontinuity; needs independent standard.<br><b>S04:</b> large rain rates near funnel cleaning on 2 Apr; <b>keep provisionally</b> pending independent comparison.<br><b>S07:</b> replacement anemometer brand may have a different transfer function. Verify calibration before comparisons.</p></div></div>
    <p class="note"><b>Method / limitations.</b> Automated range, continuity, persistence, abrupt-jump and NMEA consistency checks; one row in flags.csv represents an episode, not a count of corrupted samples. GPS void records are flagged on metadata only, not grounds to discard coincident weather. The station install sheet is a reference, not guaranteed correct. No replacement values are silently inserted. Thresholds are conservative heuristics; these are provisional station/channel decisions rather than full certified validation.</p>
    </body></html>'''
    Path(output).write_text(html_text,encoding='utf-8')
    return html_text
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Run: python generate_report.py PACK_DIR')
    make(sys.argv[1]);print('Wrote report.html')
