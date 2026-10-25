#!/usr/bin/env python3
"""Optional local visual explorer for the Ridgeline weather-quality assignment.

Start: streamlit run app.py
This does not replace the CLI checker or the required A4 report.
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from checker import COLUMNS, WEATHER, examine, write_flags
from generate_report import make as generate_report

st.set_page_config(page_title="Ridgeline | Weather Intelligence", page_icon="🌤️", layout="wide", initial_sidebar_state="expanded")

STYLES = """
<style>

:root{--ink:#172738;--muted:#617489;--teal:#0f857d;--edge:#e3eaf0;--canvas:#f6f8fb;}
html,body,[class*="css"],.stApp{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}
.stApp{background:var(--canvas);color:var(--ink)}
.block-container{padding-top:1.25rem;padding-bottom:2rem;max-width:1480px}
h1,h2,h3{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:-.035em}
h3{font-size:1.12rem!important}
section[data-testid="stSidebar"]{background:#0f2637;border-right:0}
section[data-testid="stSidebar"] *{color:#eef6f8!important}
section[data-testid="stSidebar"] input{color:#182b3a!important;background:#fff!important}
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"]{color:#d3e1ea!important}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#aac0cc!important}
[data-testid="stMetric"]{background:white;border:1px solid var(--edge);padding:18px 20px;border-radius:16px;box-shadow:0 3px 14px rgba(28,50,70,.035);min-height:114px}
[data-testid="stMetricLabel"]{color:#65778a!important;font-weight:650}
[data-testid="stMetricValue"]{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#172b3c;font-weight:800;letter-spacing:-.04em}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:.4rem;background:#eaf0f4;border-radius:12px;padding:5px;overflow-x:auto}
[data-testid="stTabs"] button[role="tab"]{border-radius:9px;padding:9px 17px;font-weight:700;color:#52697b}
[data-testid="stTabs"] button[aria-selected="true"]{background:white;color:#0f7776;box-shadow:0 1px 6px #b9cad44d}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:16px}
[data-testid="stDataFrame"]{border:1px solid #e1e9ef;border-radius:12px;overflow:hidden}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{background:#0c817b;border:0;border-radius:10px;font-weight:750}
.stButton>button{border-radius:10px}
.hero{padding:30px 35px;background:radial-gradient(ellipse at 94% 10%,#32798b 0%,transparent 38%),linear-gradient(115deg,#112638 2%,#164659 100%);color:white;border-radius:20px;margin-bottom:20px;position:relative;overflow:hidden;box-shadow:0 10px 25px #173d4b16}
.hero h1{color:white;margin:4px 0 7px;font-size:2.25rem;line-height:1.15;font-weight:800}
.hero p{color:#c8e0e8;margin:0;font-size:1rem}
.kicker{color:#76e1d0;letter-spacing:.17em;font-size:.72rem;font-weight:800;text-transform:uppercase}
.section-title{font-weight:800;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:1.12rem;color:#1b3545;margin:14px 0 10px}
.small-note{background:#fff8e8;border:1px solid #eddfbb;padding:14px 17px;border-radius:12px;color:#66532e;line-height:1.55}
.summary-note{background:#eaf7f5;border:1px solid #c8e5df;border-radius:12px;padding:16px 18px;color:#285d58;margin:4px 0 16px}
.stat-chip{background:#edf6f5;border:1px solid #d2e8e4;border-radius:8px;color:#126c66;padding:5px 9px;font-size:.79rem;font-weight:750}
.page-label{font-size:.77rem;font-weight:800;color:#73889b;letter-spacing:.11em;text-transform:uppercase;margin-bottom:.4rem}
@media(max-width:720px){.hero{padding:24px 20px}.hero h1{font-size:1.65rem}}
@media print{section[data-testid="stSidebar"]{display:none}}
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)

UNITS = {
    'temp_c':'°C', 'rh_pct':'%', 'pressure_hpa':'hPa', 'wind_kmh':'km/h',
    'wind_dir_deg':'°', 'rain_mm':'mm / 10 min', 'ghi_wm2':'W/m²'
}
NAMES = {
    'temp_c':'Temperature', 'rh_pct':'Humidity', 'pressure_hpa':'Pressure',
    'wind_kmh':'Wind speed', 'wind_dir_deg':'Wind direction',
    'rain_mm':'Rainfall', 'ghi_wm2':'Solar irradiance'
}

@st.cache_data(show_spinner=False)
def analyze(folder: str, marker: tuple):
    # Immutable cached data for a selected folder; marker reflects input modification times.
    flags, stats, all_data, stations = examine(folder)
    frame = pd.DataFrame(flags, columns=COLUMNS)
    return frame, stats, all_data, stations


def signature(folder: Path) -> tuple:
    """Cache key based on input-file timestamps, not hardcoded dataset incidents."""
    files = [folder / 'stations.csv', folder / 'maintenance_log.md']
    files += sorted((folder / 'data').glob('*.csv')) if (folder / 'data').is_dir() else []
    files += sorted((folder / 'gps').glob('*.nmea')) if (folder / 'gps').is_dir() else []
    return tuple((str(p.relative_to(folder)), p.stat().st_size, p.stat().st_mtime_ns) for p in files if p.exists())


def chart(data: pd.DataFrame, channel: str, marks: pd.DataFrame | None = None):
    thin = data.iloc[::max(1, len(data) // 4500)].copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=thin['t'], y=thin[channel], mode='lines',
                             line={'color':'#0e8b84','width':2}, name=NAMES[channel]))
    if marks is not None and not marks.empty:
        # Only use matching station/channel; episodes are shaded, not inflated into points.
        for _, row in marks.head(45).iterrows():
            a = pd.to_datetime(row['start_utc'], utc=True, errors='coerce')
            b = pd.to_datetime(row['end_utc'], utc=True, errors='coerce')
            if pd.isna(a) or pd.isna(b):
                continue
            if a == b:
                b = a + pd.Timedelta(minutes=10)
            fig.add_vrect(x0=a, x1=b, fillcolor='#e77c45' if row['action']=='exclude' else '#e9bb4a',
                          opacity=.17, line_width=0)
    fig.update_layout(height=370, margin=dict(l=10,r=15,t=15,b=10),
                      yaxis_title=f"{NAMES[channel]} ({UNITS[channel]})", xaxis_title='UTC',
                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode='x unified',
                      font=dict(color='#334155'), showlegend=False)
    fig.update_xaxes(showgrid=True,gridcolor='#edf2f7')
    fig.update_yaxes(showgrid=True,gridcolor='#edf2f7')
    return fig


def load_report(folder: str):
    # The official report generator produces the printable coordinator brief.
    # Its specific station recommendations are explicitly designed for this supplied pack.
    out = io.StringIO()
    # make writes a file, so call it only on request with a temporary destination.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        dest = str(Path(d) / 'report.html')
        generate_report(folder, dest)
        return Path(dest).read_text(encoding='utf-8')


st.sidebar.markdown('## ◈ RIDGELINE')
st.sidebar.caption('WEATHER DATA INTELLIGENCE')
st.sidebar.divider()
st.sidebar.markdown('**01 / DATA SOURCE**')

initial = str(Path.home() / 'Downloads' / 'ridgeline_extracted')
folder_text = st.sidebar.text_input(
    'Dataset folder',
    value=initial,
    help='Folder containing stations.csv, data/, gps/, and maintenance_log.md'
)
folder = Path(os.path.expanduser(folder_text)).resolve()

if st.sidebar.button('Run quality analysis', type='primary', use_container_width=True):
    st.session_state['active_pack'] = str(folder)

valid = (folder / 'stations.csv').is_file() and (folder / 'data').is_dir()

if not valid:
    st.markdown(
        '<div class="hero"><div class="kicker">RIDGELINE / DATA QUALITY</div>'
        '<h1>Weather Intelligence</h1>'
        '<p>Find trustworthy observations, explain anomalies and prioritize repairs.</p></div>',
        unsafe_allow_html=True
    )
    st.info('Enter the path to the extracted weather dataset in the sidebar, then click Run quality analysis.')
    st.code(str(folder), language='text')
    st.caption('The selected folder must contain stations.csv and data/. No dataset is uploaded anywhere.')
    st.stop()

st.sidebar.caption('All files remain on this machine. The checker does not alter the source dataset.')
active = st.session_state.get('active_pack')

if active != str(folder):
    st.markdown(
        '<div class="hero"><div class="kicker">RIDGELINE / DATA QUALITY</div>'
        '<h1>Weather Intelligence</h1>'
        '<p>Ready to inspect your local station records.</p></div>',
        unsafe_allow_html=True
    )
    st.info('Dataset located. Click Run quality analysis in the sidebar to run the checker.')
    st.stop()


try:
    with st.spinner('Analyzing station readings, timestamps, and GPS evidence...'):
        flags, stats, weather, stations = analyze(active, signature(folder))
except Exception as exc:
    st.error(f'Could not analyze this pack: {exc}')
    st.stop()

station_ids = list(stats)
actions = flags['action'].value_counts().to_dict()
total_rows = sum(v['rows'] for v in stats.values())
missing = sum(v['missing_slots'] for v in stats.values())
duplicates = sum(v['duplicate_records'] for v in stats.values())

st.markdown('<div class="hero"><div class="kicker">DATA QUALITY CONTROL CENTER · SPRING 2025</div><h1>Weather network, clearly understood.</h1><p>Eight stations. Six weeks of observations. Every issue traced to evidence.</p></div>', unsafe_allow_html=True)
col1,col2,col3,col4,col5 = st.columns(5)
col1.metric('Stations',len(stats))
col2.metric('Weather records',f'{total_rows:,}')
col3.metric('Issue episodes',f'{len(flags):,}')
col4.metric('Missing time slots',f'{missing:,}')
col5.metric('Extra duplicate rows',f'{duplicates:,}')

st.markdown('<div class="small-note">Flag counts represent <b>episodes, not bad observations</b>. These are rule-based quality checks, not a trained AI model. A flag must be weighed against weather conditions, metadata and maintenance evidence.</div>', unsafe_allow_html=True)
st.write('')

tabs = st.tabs(['◫ Overview','⌁ Station explorer','⚑ Issue flags','◎ GPS & maintenance','✣ Decisions & export'])

with tabs[0]:
    a,b = st.columns([1.45,1])
    with a:
        st.markdown('<div class="page-label">NETWORK / ALL SITES</div>',unsafe_allow_html=True)
        st.subheader('Station snapshot')
        overview=[]
        for _,m in stations.iterrows():
            sid=str(m['station_id']); f=flags[flags.station_id==sid]
            overview.append({'Station':sid, 'Name':str(m.get('name',sid)), 'Records':stats[sid]['rows'],
                             'Exclude episodes':int((f.action=='exclude').sum()), 'Keep episodes':int((f.action=='keep').sum()),
                             'Missing slots':stats[sid]['missing_slots'], 'Duplicate rows':stats[sid]['duplicate_records']})
        st.dataframe(pd.DataFrame(overview),hide_index=True,use_container_width=True)
        st.caption('These counts do not directly measure station reliability; a single prolonged episode may affect more observations than many isolated flags.')
    with b:
        st.markdown('<div class="page-label">ACTION DISTRIBUTION</div>',unsafe_allow_html=True)
        st.subheader('Flag decisions')
        fig=go.Figure(data=[go.Bar(x=list(actions),y=list(actions.values()),marker_color=['#c85a4d' if k=='exclude' else '#d7a14a' if k=='keep' else '#3b9f8c' for k in actions])])
        fig.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=20),xaxis_title='Decision',yaxis_title='Flag episodes',plot_bgcolor='white')
        st.plotly_chart(fig,use_container_width=True)
    st.markdown('<div class="page-label">INTERPRETATION GUIDE</div>',unsafe_allow_html=True)
    st.subheader('Read the evidence before acting')
    st.info('The original A4 report recommends a one-hour visit to S06 based on its timekeeping problem. This is a human-reviewed recommendation for the supplied pack, not an automated ranking based on flag counts.')
    st.markdown('<div class="page-label">HOW FLAGS ARE DISTRIBUTED</div>',unsafe_allow_html=True)
    by_station = flags.groupby(['station_id','action']).size().unstack(fill_value=0).reindex(station_ids, fill_value=0)
    fig_station = go.Figure()
    for key, color in [('exclude','#d36c61'),('correct','#268d86'),('keep','#d5a54a')]:
        if key in by_station.columns:
            fig_station.add_trace(go.Bar(name=key.title(),x=by_station.index,y=by_station[key],marker_color=color))
    fig_station.update_layout(barmode='stack',height=285,margin=dict(l=5,r=15,t=15,b=5),
                              paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                              legend=dict(orientation='h',y=1.15),yaxis_title='Flag episodes',
                              xaxis_title='Station',font=dict(color='#52697b'))
    fig_station.update_yaxes(gridcolor='#e5edf1')
    st.plotly_chart(fig_station,use_container_width=True)
    st.caption('Stacked bars count issue episodes, not failed readings or calibrated risk levels.')

with tabs[1]:
    st.markdown('<div class="page-label">DEEP DIVE / SENSOR DATA</div>',unsafe_allow_html=True)
    st.subheader('Station explorer')
    x,y=st.columns([1,2])
    sid=x.selectbox('Station',station_ids)
    ch=y.selectbox('Weather channel', WEATHER,format_func=lambda s:f'{NAMES[s]} ({UNITS[s]})')
    data=weather[sid]
    issues=flags[(flags.station_id==sid)&(flags.channel==ch)]
    st.caption(f"Inspecting {sid} · {NAMES[ch]} · anomalies shaded on the time series")
    x1,x2,x3=st.columns(3)
    x1.metric('Weather readings',f"{len(data):,}")
    x2.metric('Missing 10-min slots',f"{stats[sid]['missing_slots']:,}")
    x3.metric('Duplicate time rows',f"{stats[sid]['duplicate_records']:,}")
    st.plotly_chart(chart(data,ch,issues),use_container_width=True)
    c1,c2,c3=st.columns(3)
    c1.metric('Valid numeric samples',f'{int(data[ch].count()):,}')
    c2.metric('Channel flag episodes',len(issues))
    c3.metric('Data coverage',f"{data['t'].min().strftime('%d %b %Y')} – {data['t'].max().strftime('%d %b %Y')}")
    st.caption('Shaded intervals mark up to the first 45 matching flags. Downsampling is used only for graph speed, not detection.')
    if len(issues):
        st.dataframe(issues[['start_utc','end_utc','issue','action','note']],hide_index=True,use_container_width=True)
    else:
        st.success('No episode flags for this station and channel under the current checker rules.')

with tabs[2]:
    st.markdown('<div class="page-label">AUDIT TRAIL / REVIEW & EXPORT</div>',unsafe_allow_html=True)
    st.subheader('Detected issue episodes')
    c1,c2,c3=st.columns(3)
    fs=c1.multiselect('Stations',station_ids,default=station_ids)
    fac=c2.multiselect('Actions',['exclude','correct','keep'],default=['exclude','correct','keep'])
    all_channels=sorted(flags.channel.dropna().unique().tolist())
    fc=c3.multiselect('Channels',all_channels,default=all_channels)
    filtered=flags[flags.station_id.isin(fs)&flags.action.isin(fac)&flags.channel.isin(fc)]
    st.caption(f'{len(filtered)} matching flag episodes')
    st.dataframe(filtered,hide_index=True,use_container_width=True,height=420)
    st.download_button('⬇ Download filtered flags.csv',filtered.to_csv(index=False).encode('utf-8'),file_name='filtered_flags.csv',mime='text/csv')
    st.download_button('⬇ Download complete flags.csv',flags[COLUMNS].to_csv(index=False).encode('utf-8'),file_name='flags.csv',mime='text/csv')
    st.caption('The canonical assignment output is created by `python checker.py PACK_DIR` in the current directory. Downloads here are for exploration.')

with tabs[3]:
    st.markdown('<div class="page-label">SATELLITE DATA / LOGGER CLOCKS</div>',unsafe_allow_html=True)
    st.subheader('GPS and time integrity')
    rows=[]
    for sid in station_ids:
        g=stats[sid].get('gps') or {}
        rows.append({'Station':sid,'NMEA lines':g.get('total'),'Valid fixes':g.get('valid'),
                     'Void/malformed':g.get('void'),'Far from install (>1 km)':g.get('far'),
                     'Clock mismatch (>120s)':g.get('clock')})
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.caption('GPS counts represent sampled NMEA records, not weather readings. The install sheet may also contain errors.')
    st.subheader('Maintenance notebook')
    log=folder/'maintenance_log.md'
    if log.exists():
        st.markdown(log.read_text(encoding='utf-8'))
    else:
        st.warning('No maintenance_log.md file found.')

with tabs[4]:
    st.markdown('<div class="page-label">FIELD ACTION PLAN / REPORTING</div>',unsafe_allow_html=True)
    st.subheader('Coordinator decision support')
    st.markdown('**Recommended initial visit: S06** — investigate the logger/GPS clock discrepancy after the battery change. The existing coordinator report compares S06 with S05 and gives a practical hour-long inspection plan.')
    st.warning('This recommendation is taken from the original evidence-based report for this pack. It is not automatically recomputed for arbitrary new datasets. Reassess it when using a different pack.')
    st.markdown('**One-hour visit outline**')
    st.markdown('1. **0–10 min:** Record the current logger UTC time, GPS fix, and power status before resetting anything.\n2. **10–25 min:** Compare raw NMEA UTC against logger UTC; inspect time-zone and clock-source settings.\n3. **25–40 min:** Check battery connections and reboot/buffer logs.\n4. **40–55 min:** Record side-by-side timestamps against a trusted UTC source.\n5. **55–60 min:** Document offsets, evidence, and whether recovery is justified.')
    st.divider()
    st.subheader('Official printable report')
    try:
        content=load_report(active)
        st.download_button('⬇ Download A4 network report (HTML)',content.encode('utf-8'),file_name='report.html',mime='text/html')
        st.caption('The HTML is formatted for A4 printing: open it in your browser and choose Print → Save as PDF.')
    except Exception as exc:
        st.error(f'Report could not be generated: {exc}')

st.divider()
st.caption('Local-only assignment explorer. No uploads, external APIs, location tracking, trained ML, or automatic changes to source data. Keep the private data pack out of public GitHub repositories.')
