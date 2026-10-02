"""Acquire real OSM green/commercial comparison polygons in Tanager footprints.

Run --fetch to save OSM candidates. Run --extract after downloading the three
Tanager ortho_sr HDF5 scenes; only clear, separated sites yield new spectra.
OSM tags and polygon geometry are proxy labels, not field verification.
"""
import argparse,json,math
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BOXES={'Jacksonville':(-81.69369938031545,30.259070621905575,-81.45079750932877,30.439677039738726),
'Rochester':(-77.7151722184759,43.06303136820783,-77.40833399105284,43.259199834613476),
'Detroit':(-83.33175247670914,42.14831477016702,-83.01418472462309,42.40408910830337)}
SCENES={'Jacksonville':'20250516_164837_16_4001','Rochester':'20250801_165548_86_4001','Detroit':'20250914_171527_18_4001'}
SNAP=ROOT/'data/source_snapshots';OUTPUT=ROOT/'data/candidate_controls.csv'
def distance(a,b):
 lat1,lon1=a;lat2,lon2=b;dl=math.radians(lat2-lat1);dn=math.radians(lon2-lon1)
 return 12742000*math.asin(min(1,math.sqrt(math.sin(dl/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dn/2)**2)))
def category(tags):
 if tags.get('leisure')=='park' or tags.get('landuse') in ('forest','grass','recreation_ground'):return 'green_space'
 if tags.get('landuse') in ('commercial','retail') or tags.get('building') in ('commercial','retail','office'):return 'commercial'
 return None
def fetch():
 import requests
 from shapely.geometry import Polygon
 rows=[]
 for city,(west,south,east,north) in BOXES.items():
  # OSM ways are requested as full geometry; no synthetic locations.
  q=f'''[out:json][timeout:180];(way["leisure"="park"]({south},{west},{north},{east});way["landuse"~"^(forest|grass|recreation_ground|commercial|retail)$"]({south},{west},{north},{east});way["building"~"^(commercial|retail|office)$"]({south},{west},{north},{east}););out geom;'''
  response=requests.post('https://overpass-api.de/api/interpreter',data={'data':q},timeout=240)
  response.raise_for_status();payload=response.json()
  (SNAP/f'osm_landuse_{city.lower()}.json').write_text(json.dumps(payload))
  for feature in payload.get('elements',[]):
   tags=feature.get('tags',{});kind=category(tags);geometry=feature.get('geometry',[])
   if not kind or len(geometry)<4:continue
   shape=Polygon([(p['lon'],p['lat']) for p in geometry])
   if not shape.is_valid:shape=shape.buffer(0)
   if shape.is_empty:continue
   point=shape.representative_point();lat,lon=point.y,point.x
   if not (west+.002<lon<east-.002 and south+.002<lat<north-.002):continue
   # Minimize mixed pixels: the green center should have ~90m interior clearance.
   # Commercial centers may be small and remain neighborhood-context labels.
   clearance=shape.boundary.distance(point)*111000
   if kind=='green_space' and clearance<90:continue
   if kind=='commercial' and clearance<20:continue
   rows.append({'facility_id':f"OSM_way_{feature['id']}",'name':tags.get('name',f'{kind} OSM way {feature["id"]}'),
    'city':city,'latitude':lat,'longitude':lon,'site_type':kind,'scene_id':SCENES[city],
    'polygon_clearance_approx_m':round(clearance,1),'status':'candidate_needs_Tanager_QA_and_visual_label_check',
    'source_url':f"https://www.openstreetmap.org/way/{feature['id']}"})
 candidates=pd.DataFrame(rows).drop_duplicates('facility_id').sort_values(['city','site_type','facility_id'])
 candidates.to_csv(OUTPUT,index=False)
 print(f'Saved {len(candidates)} real OSM polygon candidates to {OUTPUT}')
 print(candidates.groupby(['city','site_type']).size().to_string())
def extract():
 import h5py
 from src.train_classifier import site_features
 candidates=pd.read_csv(OUTPUT,dtype={'facility_id':str,'scene_id':str})
 observed=pd.read_csv(ROOT/'results/real/classifier/site_spectral_features.csv',dtype={'facility_id':str,'scene_id':str})
 existing=list(zip(observed.latitude.astype(float),observed.longitude.astype(float)))
 additions=[]
 for city in BOXES:
  scene=SCENES[city];source=ROOT/'data/cache'/f'{scene}_ortho_sr.h5'
  if not source.exists():raise FileNotFoundError(f'{source}: run python -m src.multisite_download first')
  with h5py.File(source) as h:
   for kind in ('green_space','commercial'):
    group=candidates[(candidates.city==city)&(candidates.site_type==kind)]
    taken=0
    for _,site in group.iterrows():
     coords=(float(site.latitude),float(site.longitude))
     if any(distance(coords,other)<650 for other in existing):continue
     try:features=site_features(h,*coords)
     except (ValueError,IndexError):continue
     if sum(not math.isfinite(v) for v in features.values())>5:continue
     additions.append({'facility_id':site.facility_id,'name':site['name'],'city':city,'latitude':coords[0],
      'longitude':coords[1],'label':0,'site_type':kind,'scene_id':scene,'source_url':site.source_url,
      'validation_status':'OSM_polygon_proxy; visually verify land use before operational model',**features})
     existing.append(coords);taken+=1
     if taken>=4:break
    print(city,kind,'QA-passing new controls:',taken)
 if not additions:raise RuntimeError('No QA-passing new controls; inspect OSM polygons and source imagery')
 combined=pd.concat([observed,pd.DataFrame(additions)],ignore_index=True)
 out=ROOT/'results/real/classifier/site_spectral_features_expanded.csv'
 combined.to_csv(out,index=False)
 print('Saved',out,'observed rows',len(combined),'new controls',len(additions))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--fetch',action='store_true');parser.add_argument('--extract',action='store_true');args=parser.parse_args()
 if args.fetch:fetch()
 if args.extract:extract()
 if not (args.fetch or args.extract):parser.error('Specify --fetch or --extract')
