"""Three-city CAMS regional air context and ERA5 10 m wind, scene-week dates."""
from pathlib import Path
import pandas as pd
from pipeline import air_context
from wind import fetch_wind
REGIONS={
 'Jacksonville':([-81.69369938031545,30.259070621905575,-81.45079750932877,30.439677039738726],'2025-05-16','2025-05-22',30.34,-81.648),
 'Rochester':([-77.7151722184759,43.06303136820783,-77.40833399105284,43.259199834613476],'2025-08-01','2025-08-07',43.15,-77.62),
 'Detroit':([-83.33175247670914,42.14831477016702,-83.01418472462309,42.40408910830337],'2025-09-14','2025-09-20',42.29,-83.15)}
def analyze(out='results/real'):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);air_rows=[];wind_rows=[]
 for city,(bbox,start,end,lat,lon) in REGIONS.items():
  air,_=air_context(bbox,start,end);wind,_=fetch_wind(lat,lon,start,end)
  air.insert(0,'city',city);wind.insert(0,'city',city)
  air_rows.append(air);wind_rows.append(wind)
 pd.concat(air_rows).to_csv(out/'air_by_city.csv',index=False)
 pd.concat(wind_rows).to_csv(out/'wind_by_city.csv',index=False)
 return pd.concat(air_rows),pd.concat(wind_rows)
if __name__=='__main__':
 a,w=analyze();print('CAMS hours',len(a),'ERA5 hours',len(w))
