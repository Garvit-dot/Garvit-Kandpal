import csv
from pathlib import Path
import sys
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from checker import examine,write_flags,episodes,nmea_coord,haversine,COLUMNS

def make_pack(tmp_path,station='T91'):
    d=tmp_path/'data';d.mkdir()
    (tmp_path/'gps').mkdir()
    (tmp_path/'stations.csv').write_text('station_id,name,lat,lon,elevation_m,installed,logger_interval_min\n'+f'{station},Test,40.0,-105.0,1000,2025-01-01,10\n')
    times=pd.date_range('2025-02-01',periods=24*6,freq='10min',tz='UTC')
    frame=pd.DataFrame({'timestamp_utc':times.strftime('%Y-%m-%d %H:%M'),'temp_c':list(range(24))*6,'rh_pct':50,'pressure_hpa':900,'wind_kmh':5,'wind_dir_deg':90,'rain_mm':0,'ghi_wm2':100})
    frame.to_csv(d/f'{station}.csv',index=False)
    return frame

def test_nominal_pack(tmp_path):
    make_pack(tmp_path)
    f,s,_,_=examine(tmp_path)
    assert 'T91' in s and s['T91']['missing_slots']==0
    p=tmp_path/'flags.csv';write_flags(f,p)
    with p.open() as fp: assert next(csv.reader(fp))==COLUMNS

def test_duplicate_missing(tmp_path):
    a=make_pack(tmp_path)
    a=pd.concat([a.drop(index=[3]),a.iloc[[5]]],ignore_index=True)
    a.to_csv(tmp_path/'data/T91.csv',index=False)
    f,_,_,_=examine(tmp_path)
    assert {'Duplicate logger timestamps','Missing logger intervals'}.issubset({x['issue'] for x in f})

def test_humidity_bounds(tmp_path):
    a=make_pack(tmp_path);a.loc[4,'rh_pct']=104
    a.to_csv(tmp_path/'data/T91.csv',index=False)
    f,_,_,_=examine(tmp_path)
    assert any(x['channel']=='rh_pct' and x['action']=='exclude' for x in f)

def test_temperature_spike(tmp_path):
    a=make_pack(tmp_path);a.loc[20,'temp_c']=85
    a.to_csv(tmp_path/'data/T91.csv',index=False)
    f,_,_,_=examine(tmp_path)
    assert any(x['issue']=='Abrupt temperature jump' for x in f)

def test_flatline(tmp_path):
    a=make_pack(tmp_path);a['temp_c']=7.5
    a.to_csv(tmp_path/'data/T91.csv',index=False)
    f,_,_,_=examine(tmp_path)
    assert any(x['issue']=='Prolonged exact-value flatline' for x in f)

def test_realistic_extreme_unchanged(tmp_path):
    a=make_pack(tmp_path);a['temp_c']=pd.Series(range(144))*0.1-20
    a.to_csv(tmp_path/'data/T91.csv',index=False)
    f,_,_,_=examine(tmp_path)
    assert not any(x['issue']=='Outside physical plausibility bounds' and x['channel']=='temp_c' for x in f)

def test_void_gps(tmp_path):
    make_pack(tmp_path)
    (tmp_path/'gps/T91.nmea').write_text('2025-02-01 00:00:01,$GPRMC,000000.00,V,4000.0000,N,10500.0000,W,0,0,010225,,,N*00\n')
    f,_,_,_=examine(tmp_path)
    assert any(x['issue']=='GPS void/malformed fixes' for x in f)

def test_far_gps(tmp_path):
    make_pack(tmp_path)
    (tmp_path/'gps/T91.nmea').write_text('2025-02-01 00:00:01,$GPRMC,000000.00,A,4100.0000,N,10500.0000,W,0,0,010225,,,A*00\n')
    f,_,_,_=examine(tmp_path)
    assert any(x['issue']=='GPS installation mismatch' for x in f)

def test_other_pack_station(tmp_path):
    make_pack(tmp_path,station='ABC77')
    f,stats,_,_=examine(tmp_path)
    assert list(stats)==['ABC77']

def test_missing_required_column(tmp_path):
    a=make_pack(tmp_path).drop(columns=['rain_mm'])
    a.to_csv(tmp_path/'data/T91.csv',index=False)
    with pytest.raises(ValueError,match='missing columns'):examine(tmp_path)

def test_missing_csv(tmp_path):
    make_pack(tmp_path)
    (tmp_path/'data/T91.csv').unlink()
    with pytest.raises(ValueError,match='Missing weather file'):examine(tmp_path)

def test_episode_gap():
    t=pd.to_datetime(['2025-01-01 00:00','2025-01-01 00:10','2025-01-01 00:40'],utc=True)
    assert len(episodes([1,1,1],t))==2

def test_nmea_coordinates():
    assert nmea_coord('4000.0000','N')==40
    assert nmea_coord('10500.0000','W')==-105
    assert haversine(40,-105,40,-105)<0.001
