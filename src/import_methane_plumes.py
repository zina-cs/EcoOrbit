"""Match exported Carbon Mapper CH4 or CO2 plumes to registered case sites.

Source file: Carbon Mapper data portal plume list. Preserve original identifiers,
quality, instrument, wind and emission uncertainty. No estimated rates invented.
"""
import argparse,json,math
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/real/methane'
def distance(lat1,lon1,lat2,lon2):
 p=math.pi/180;dl=(lat2-lat1)*p;dn=(lon2-lon1)*p
 return 12742*math.asin(min(1,math.sqrt(math.sin(dl/2)**2+math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dn/2)**2)))
def load(path):
 path=Path(path)
 if path.suffix.lower() in ('.geojson','.json'):
  payload=json.loads(path.read_text());items=payload.get('features',payload.get('items',[]))
  rows=[]
  for f in items:
   row=dict(f.get('properties',f));coords=f.get('geometry',{}).get('coordinates') or row.get('geometry_json',{}).get('coordinates')
   if coords and len(coords)>=2:row.update(longitude=coords[0],latitude=coords[1])
   rows.append(row)
  return pd.DataFrame(rows)
 return pd.read_csv(path)
def published():
 """Materialize the bundled, source-linked real CH4/CO2 observations."""
 d=pd.read_csv(ROOT/'data/published_plumes.csv')
 required={'plume_id','gas','scene_timestamp','reported_rate_kg_h','source_url'}
 if not required.issubset(d):raise ValueError('Published plume register is missing required columns')
 if d.plume_id.duplicated().any() or not d.gas.isin(['CH4','CO2']).all() or d.reported_rate_kg_h.isna().any():
  raise ValueError('Published plume metadata is incomplete')
 OUT.mkdir(parents=True,exist_ok=True)
 d.to_csv(OUT/'published_plume_results.csv',index=False)
 print('Validated',len(d),'source-linked published CH4/CO2 plume examples; target-case attribution not implied')
 return d

def run(path,output=None):
 data=load(path);sites=pd.read_csv(ROOT/'data/methane_sites.csv')
 def field(row,*names):
  for name in names:
   v=row.get(name)
   if v is not None and not isinstance(v,(list,dict)) and pd.notna(v) and str(v).strip():return v
  return None
 records=[]
 for _,r in data.iterrows():
  lat=field(r,'latitude','plume_latitude','lat');lon=field(r,'longitude','plume_longitude','lon')
  if lat is None or lon is None:continue
  lat=float(lat);lon=float(lon)
  site=sites.iloc[min(range(len(sites)),key=lambda j:distance(lat,lon,float(sites.iloc[j].latitude),float(sites.iloc[j].longitude)))]
  km=distance(lat,lon,float(site.latitude),float(site.longitude))
  if km>20:continue
  gas=str(field(r,'gas','gas_type') or 'CH4').upper()
  if gas not in ('CH4','METHANE','CO2','CARBON DIOXIDE'):continue
  gas='CH4' if gas in ('CH4','METHANE') else 'CO2'
  records.append({'site_id':site.site_id,'site_name':site['name'],'gas':gas,'plume_id':field(r,'plume_id','plume_name','id'),
   'scene_timestamp':field(r,'scene_timestamp','acquisition_time','date'),
   'plume_latitude':lat,'plume_longitude':lon,'site_distance_km':round(km,2),
   'instrument':field(r,'instrument','platform'),'sector':field(r,'sector'),
   'instantaneous_emission_kg_h':field(r,'emission_auto','emission_kg_h'),
   'emission_uncertainty_kg_h':field(r,'emission_uncertainty_auto','emission_uncertainty_kg_h'),
   'wind_speed_m_s':field(r,'wind_speed_avg_auto','wind_speed_m_s'),
   'wind_direction_deg':field(r,'wind_direction_avg_auto','wind_direction_deg'),
   'plume_quality':field(r,'plume_quality','quality'),
   'status':'near_site_plume_candidate_requires_source_and_quality_review'})
 OUT.mkdir(parents=True,exist_ok=True);result=pd.DataFrame(records,columns=['site_id','site_name','gas','plume_id','scene_timestamp','plume_latitude','plume_longitude','site_distance_km','instrument','sector','instantaneous_emission_kg_h','emission_uncertainty_kg_h','wind_speed_m_s','wind_direction_deg','plume_quality','status'])
 result.to_csv(Path(output) if output else OUT/'plume_matches.csv',index=False)
 print('Matched',len(result),'CH4/CO2 plume records within 20 km; proximity is not source attribution')
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('file',nargs='?',help='Exported Carbon Mapper plume CSV or GeoJSON');parser.add_argument('--published',action='store_true',help='Build the bundled real published plume result without network or credentials');args=parser.parse_args()
 if args.published:published()
 elif args.file:run(args.file)
 else:parser.error('provide a plume export file or --published')
