#!/usr/bin/env python3
"""Ridgeline weather network quality checker. Usage: python checker.py PACK_DIR"""
import argparse
import csv
import math
import re
from pathlib import Path
import numpy as np
import pandas as pd

COLUMNS=['station_id','channel','start_utc','end_utc','issue','action','note']
WEATHER=['temp_c','rh_pct','pressure_hpa','wind_kmh','wind_dir_deg','rain_mm','ghi_wm2']
BOUNDS={'temp_c':(-60,60),'rh_pct':(0,100),'pressure_hpa':(450,1100),'wind_kmh':(0,250),'wind_dir_deg':(0,360),'rain_mm':(0,250),'ghi_wm2':(0,1500)}

def fmt(t): return pd.Timestamp(t).strftime('%Y-%m-%d %H:%M')
def flag(out,s,c,a,b,issue,action,note):
    out.append(dict(station_id=s,channel=c,start_utc=fmt(a),end_utc=fmt(b),issue=issue,action=action,note=note))

def episodes(mask, times, max_gap='10min', min_n=1):
    """Group true elements of chronologically sorted series, with a fixed sampling-gap tolerance."""
    z=pd.DataFrame({'t':pd.to_datetime(times),'ok':np.asarray(mask,dtype=bool)})
    z=z[z.ok].sort_values('t')
    if z.empty:return []
    group=(z.t.diff()>pd.Timedelta(max_gap)).cumsum()
    return [(v.t.iloc[0],v.t.iloc[-1],len(v)) for _,v in z.groupby(group) if len(v)>=min_n]

def nmea_coord(raw,hem):
    try:
        x=float(raw);deg=math.floor(x/100); minute=x-100*deg
        if minute>=60 or hem not in 'NSEW':return None
        return (deg+minute/60)*(-1 if hem in 'SW' else 1)
    except (ValueError,TypeError):return None

def haversine(a,b,c,d):
    r1,r2=math.radians(a),math.radians(c);dr=r2-r1;dl=math.radians(d-b)
    return 6371*2*math.asin(min(1,math.sqrt(math.sin(dr/2)**2+math.cos(r1)*math.cos(r2)*math.sin(dl/2)**2)))

def gps_checks(path,station,lat,lon,out,observed_start=None,observed_end=None):
    if not path.exists():
        flag(out,station,'metadata',observed_start,observed_end,'GPS file missing','exclude','No GPS file; logger clock and location cannot be independently validated.')
        return
    bad=[];far=[];clock=[];valid=0;total=0
    with path.open(errors='replace') as f:
        for line in f:
            total+=1
            parts=line.strip().split(',',1)
            if len(parts)<2:continue
            ts=pd.to_datetime(parts[0],errors='coerce',utc=True)
            if pd.isna(ts):continue
            p=parts[1].split(',');type_=p[0][-3:]
            if type_ not in ('RMC','GGA'):continue
            try:
                if type_=='RMC':
                    ok=len(p)>=10 and p[2]=='A'; la=nmea_coord(p[3],p[4]);lo=nmea_coord(p[5],p[6]);time=p[1];date=p[9]
                else:
                    ok=len(p)>=10 and int(p[6])>0;la=nmea_coord(p[2],p[3]);lo=nmea_coord(p[4],p[5]);time=p[1];date=None
                if not ok or la is None or lo is None:bad.append(ts);continue
                valid+=1
                dist=haversine(lat,lon,la,lo)
                if dist>1:far.append((ts,dist))
                if len(time)>=6 and time[:6].isdigit():
                    hour,minute,sec=int(time[:2]),int(time[2:4]),int(time[4:6]);
                    gps_time=ts.normalize()+pd.Timedelta(hours=hour,minutes=minute,seconds=sec)
                    if date and len(date)==6 and date.isdigit():
                        try:gps_time=pd.Timestamp(year=2000+int(date[4:6]),month=int(date[2:4]),day=int(date[:2]),hour=hour,minute=minute,second=sec,tz='UTC')
                        except ValueError:pass
                    if type_=='GGA':
                        opts=[gps_time-pd.Timedelta(days=1),gps_time,gps_time+pd.Timedelta(days=1)]
                        gps_time=min(opts,key=lambda a:abs((ts-a).total_seconds()))
                    delta=(ts-gps_time).total_seconds()
                    if abs(delta)>120:clock.append((ts,delta))
            except (ValueError,IndexError,OverflowError):bad.append(ts)
    for kind,items,note,action in [
      ('GPS void/malformed fixes',bad,'NMEA fix invalid, void or malformed; location and time reference unavailable for these records.','exclude'),
      ('GPS installation mismatch',far,'Valid GPS coordinates are >1 km from installation sheet; verify installation/receiver, not weather values.','exclude'),
      ('GPS/logger clock disagreement',clock,'Absolute logger-to-NMEA UTC discrepancy >120 seconds; verify logger clock alignment before aggregating.','exclude')]:
        times=[x[0] if isinstance(x,tuple) else x for x in items]
        for a,b,n in episodes([True]*len(times),times,max_gap='3h'):
            extra=''
            if kind=='GPS installation mismatch':extra=f' Peak {max(v for t,v in items if a<=t<=b):.1f} km.'
            if kind=='GPS/logger clock disagreement':extra=f' Peak {max(abs(v) for t,v in items if a<=t<=b):.0f} s.'
            flag(out,station,'metadata',a,b,kind,action,f'{n} {note}{extra}')
    return {'total':total,'valid':valid,'void':len(bad),'far':len(far),'clock':len(clock)}

def examine(pack):
    pack=Path(pack);meta=pack/'stations.csv';data=pack/'data'
    if not meta.is_file() or not data.is_dir():raise ValueError('Pack must contain stations.csv and data/ directory')
    stations=pd.read_csv(meta)
    required={'station_id','lat','lon','logger_interval_min'}
    if not required.issubset(stations.columns):raise ValueError(f'stations.csv missing: {sorted(required-set(stations.columns))}')
    if stations.station_id.isna().any() or stations.station_id.duplicated().any():raise ValueError('Duplicate or missing station IDs in metadata')
    out=[]; stats={};details={};all_data={}
    for _,m in stations.iterrows():
        s=str(m.station_id);file=data/f'{s}.csv';interval=int(m.logger_interval_min)
        if interval<=0:raise ValueError(f'Invalid interval for {s}')
        if not file.exists():raise ValueError(f'Missing weather file: {file}')
        d=pd.read_csv(file);missing=set(['timestamp_utc']+WEATHER)-set(d.columns)
        if missing:raise ValueError(f'{s}: missing columns: {sorted(missing)}')
        if d.empty:raise ValueError(f'{s}: weather CSV empty')
        rawts=pd.to_datetime(d.timestamp_utc,errors='coerce',utc=True)
        if rawts.isna().any():raise ValueError(f'{s}: {rawts.isna().sum()} malformed timestamps')
        if not rawts.is_monotonic_increasing:
            flag(out,s,'all',rawts.min(),rawts.max(),'Out-of-order logger records','keep','Source rows are not ordered; sorted chronologically for checking, with raw records unchanged.')
        d['t']=rawts;d=d.sort_values('t',kind='stable').reset_index(drop=True);t=d.t
        duplicates=d.t.duplicated(keep=False)
        for a,b,n in episodes(duplicates,t,max_gap=f'{interval}min'):
            flag(out,s,'all',a,b,'Duplicate logger timestamps','exclude',f'{n} records share timestamps; retain one only after confirming which readings are original.')
        u=t.drop_duplicates();miss=pd.date_range(u.iloc[0],u.iloc[-1],freq=f'{interval}min',tz='UTC').difference(pd.DatetimeIndex(u))
        for a,b,n in episodes([True]*len(miss),miss,max_gap=f'{interval}min'):
            flag(out,s,'all',a,b,'Missing logger intervals','exclude',f'{n} expected {interval}-minute observations absent; do not fill unobserved weather.')
        for c in WEATHER:
            x=pd.to_numeric(d[c],errors='coerce'); d[c]=x
            if x.isna().any():
                for a,b,n in episodes(x.isna(),t,max_gap=f'{interval}min'):
                    flag(out,s,c,a,b,'Missing or nonnumeric reading','exclude',f'{n} readings missing or invalid; omit from {c} summary.')
            low,high=BOUNDS[c];bad=(x<low)|(x>high)
            for a,b,n in episodes(bad,t,max_gap=f'{interval}min'):
                flag(out,s,c,a,b,'Outside physical plausibility bounds','exclude',f'{n} readings outside declared {low}–{high} {c} limits; values cannot be used as observed.')
            if c in ['temp_c','rh_pct','pressure_hpa','wind_kmh','ghi_wm2']:
                # A 24-hour or longer exact flatline is implausible for these dynamically varying sensors.
                runs=(x.ne(x.shift())|t.diff().gt(pd.Timedelta(minutes=interval))).cumsum()
                for _,g in d.groupby(runs):
                    if len(g)>=1440//interval and pd.notna(g[c].iloc[0]):
                        a,b=g.t.iloc[0],g.t.iloc[-1]
                        # do not repeat obviously physically impossible episode
                        if (g[c].iloc[0]<low or g[c].iloc[0]>high):continue
                        flag(out,s,c,a,b,'Prolonged exact-value flatline','exclude',f'{len(g)} consecutive values equal {g[c].iloc[0]:g}; improbable for this varying sensor.')
            if c=='temp_c':
                delta=x.diff().abs();fast=(delta>12)&t.diff().eq(pd.Timedelta(minutes=interval))
                for a,b,n in episodes(fast,t,max_gap=f'{interval}min'):
                    flag(out,s,c,a,b,'Abrupt temperature jump','exclude',f'{n} jumps exceed 12 °C in {interval} minutes; evaluate adjacent readings for corruption.')
            if c=='pressure_hpa':
                # An abrupt instrument shift is evidence; weather pressure rarely jumps >4 hPa per 10 min.
                jumps=(x.diff().abs()>4)&t.diff().eq(pd.Timedelta(minutes=interval))
                for a,b,n in episodes(jumps,t,max_gap=f'{interval}min'):
                    flag(out,s,c,a,b,'Abrupt pressure step','exclude',f'{n} pressure changes exceed 4 hPa per {interval} minutes; possible board offset or logger discontinuity.')
            if c=='rain_mm':
                # Not all rainfall spikes are faulty; a high spike requires contextual evidence to exclude.
                highrain=x>8
                for a,b,n in episodes(highrain,t,max_gap=f'{interval}min'):
                    flag(out,s,c,a,b,'Unusually large 10-minute rainfall','keep',f'{n} interval(s) >8 mm; check gauge condition and neighbouring rain before deciding exclusion.')
        # Long daytime saturated humidity with sun (not automatically excluded).
        sun=(d['ghi_wm2']>300)&(d['rh_pct']>=99)
        if int(sun.sum())>=30:
            for a,b,n in episodes(sun,t,max_gap='30min',min_n=12):
                flag(out,s,'rh_pct',a,b,'Daytime humidity saturation','keep',f'{n} readings at >=99% RH while sunlight exceeds 300 W/m²; inspect humidity calibration; fog or wet sensor remains possible.')
        gps=gps_checks(pack/'gps'/f'{s}.nmea',s,float(m.lat),float(m.lon),out,t.iloc[0],t.iloc[-1])
        all_data[s]=d
        stats[s]={'rows':len(d),'duplicate_records':int(d.t.duplicated().sum()),'missing_slots':len(miss),'gps':gps}
    return out,stats,all_data,stations

def write_flags(flags,path):
    unique={tuple(f.get(c,'') for c in COLUMNS):f for f in flags}
    ordered=sorted(unique.values(),key=lambda d:(d['station_id'],d['start_utc'],d['channel'],d['issue']))
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader();w.writerows(ordered)
    return ordered

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pack_dir',help='Unzipped pack folder containing stations.csv');args=p.parse_args()
    flags,stats,_,_=examine(args.pack_dir);rows=write_flags(flags,Path.cwd()/'flags.csv')
    print(f'Checked {len(stats)} stations; wrote {len(rows)} issue episodes to {Path.cwd()/"flags.csv"}')
if __name__=='__main__':main()
