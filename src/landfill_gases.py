"""Independent NASA EMIT CH4/CO2 plume search and OCO-2/3 regional CO2 context.

Search requires network; downloads require a personal NASA Earthdata login. No
plume is attributed to a landfill by proximity alone. No empty search is zero.
"""
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from shapely.geometry import Point, shape
from shapely.ops import nearest_points

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/real/landfill_gases'
SITES=ROOT/'data/landfill_sites.csv'
EMIT_COLUMNS=['site_id','site_name','gas','granule_id','observed_at','plume_distance_km','plume_geometry','emission_rate_reported','emission_uncertainty_reported','emission_rate_units','properties_json','metadata_file','raster_file','browse_image','status']
OCO_COLUMNS=['site_id','site_name','instrument','file','near_n','background_n','near_xco2_ppm','background_xco2_ppm','near_minus_background_ppm','status']
def km(a,b,c,d):
 p=math.pi/180;v=math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
 return 12742*math.asin(min(1,math.sqrt(v)))
def sites():return pd.read_csv(SITES)
def _geometry_km(site,geometry):
 point=Point(float(site.longitude),float(site.latitude))
 other=nearest_points(point,geometry)[1]
 return km(point.y,point.x,other.y,other.x)
def _feature_rows(payload):
 if payload.get('type')=='FeatureCollection':return payload.get('features',[])
 if payload.get('type')=='Feature':return [payload]
 if payload.get('geometry'):return [payload]
 return []
def _property(props,*names):
 for name in names:
  v=props.get(name)
  if v is not None and not isinstance(v,(dict,list)) and str(v).strip():return v
 return ''
def import_emit(directory,site_filter=None,max_km=15):
 """Read actual EMIT V002 plume GeoJSON downloaded from Earthdata."""
 directory=Path(directory);OUT.mkdir(parents=True,exist_ok=True)
 rows=[]
 for path in sorted(directory.rglob('*.json'))+sorted(directory.rglob('*.geojson')):
  if 'CH4PLM' not in path.name.upper() and 'CO2PLM' not in path.name.upper():continue
  gas='CH4' if 'CH4PLM' in path.name.upper() else 'CO2'
  payload=json.loads(path.read_text());stem=path.stem
  for feature in _feature_rows(payload):
   if not feature.get('geometry'):continue
   geometry=shape(feature['geometry']);props=feature.get('properties') or {}
   if geometry.is_empty:continue
   for site in sites().itertuples():
    if site_filter and site.site_id!=site_filter:continue
    distance=_geometry_km(site,geometry)
    if distance>max_km:continue
    raster_stem=stem.replace('PLMMETA','PLM')
    tif=next(iter(path.parent.glob(raster_stem+'*.tif')),None)
    if tif is None:tif=next(iter(path.parent.glob(raster_stem+'*.tiff')),None)
    png=next(iter(path.parent.glob(raster_stem+'*.png')),None)
    rows.append({'site_id':site.site_id,'site_name':site.name,'gas':gas,'granule_id':stem,
      'observed_at':_property(props,'time_coverage_start','datetime','timestamp') or _time_from_name(stem),
      'plume_distance_km':round(distance,3),'plume_geometry':geometry.geom_type,
      'emission_rate_reported':_property(props,'emission_rate','emission_rate_kg_hr','ime_emission_rate','emission_kg_h','emission'),
      'emission_uncertainty_reported':_property(props,'emission_uncertainty','emission_rate_uncertainty','uncertainty'),
      'emission_rate_units':_property(props,'emission_rate_units','emission_units'),
      'properties_json':json.dumps(props,default=str),
      'metadata_file':str(path),'raster_file':str(tif) if tif else '',
      'browse_image':str(png) if png else '',
      'status':'plume_outline_near_landfill_source_attribution_requires_review'})
 result=pd.DataFrame(rows,columns=EMIT_COLUMNS)
 result.to_csv(OUT/'emit_plume_candidates.csv',index=False)
 print('EMIT plume outlines within',max_km,'km:',len(result),'— proximity is not attribution')
 return result
def _time_from_name(stem):
 import re
 m=re.search(r'\d{8}T\d{6}',stem)
 return m.group() if m else ''
def search_emit(site_filter=None,start='2022-01-01',end='2026-09-29',max_granules=50,download=False):
 """Search NASA CMR by bbox, optionally download all matching plume granules."""
 import earthaccess
 OUT.mkdir(parents=True,exist_ok=True)
 rows=[];selected=[]
 for site in sites().itertuples():
  if site_filter and site.site_id!=site_filter:continue
  lat,lon=float(site.latitude),float(site.longitude)
  for gas,product in [('CH4','EMITL2BCH4PLM'),('CO2','EMITL2BCO2PLM')]:
   granules=earthaccess.search_data(short_name=product,version='002',bounding_box=(lon-.18,lat-.18,lon+.18,lat+.18),temporal=(start,end),count=max_granules)
   print(site.site_id,gas,'intersecting granules:',len(granules))
   for g in granules:
    d=dict(g);meta=d.get('meta',{});umm=d.get('umm',{})
    title=meta.get('native-id') or umm.get('GranuleUR') or ''
    urls=g.data_links() if hasattr(g,'data_links') else []
    polygons=umm.get('SpatialExtent',{}).get('HorizontalSpatialDomain',{}).get('Geometry',{}).get('GPolygons',[])
    outlines=[]
    for polygon in polygons:
     points=polygon.get('Boundary',{}).get('Points',[])
     if len(points)>=3:outlines.append([[float(p['Longitude']),float(p['Latitude'])] for p in points])
    distances=[_geometry_km(site,shape({'type':'Polygon','coordinates':[p]})) for p in outlines]
    dist=min(distances) if distances else None
    rows.append({'site_id':site.site_id,'gas':gas,'granule_id':title,'concept_id':meta.get('concept-id',''),
      'plume_distance_km':round(dist,3) if dist is not None else '',
      'plume_outline_json':json.dumps(outlines, separators=(',',':')),'data_links':' | '.join(urls),
      'status':'cmr_plume_footprint_near_site_review_source' if dist is not None and dist<=15 else 'bbox_intersection_geometry_unconfirmed'})
   selected.extend(granules)
 pd.DataFrame(rows,columns=['site_id','gas','granule_id','concept_id','plume_distance_km','plume_outline_json','data_links','status']).to_csv(OUT/'emit_search.csv',index=False)
 if download and selected:
  earthaccess.login(strategy='interactive')
  cache=ROOT/'data/cache/emit_landfills';cache.mkdir(parents=True,exist_ok=True)
  earthaccess.download(selected,str(cache))
  return import_emit(cache,site_filter)
 return pd.DataFrame(rows)
def search_oco(site_filter=None,start='2024-02-24',end='2024-02-28',max_granules=8,download=False):
 """Find OCO-2/3 Lite daily files overlapping a landfill; soundings need QA."""
 import earthaccess
 OUT.mkdir(parents=True,exist_ok=True);rows=[];selected=[]
 for site in sites().itertuples():
  if site_filter and site.site_id!=site_filter:continue
  lat,lon=float(site.latitude),float(site.longitude)
  for product in ['OCO2_L2_Lite_FP','OCO3_L2_Lite_FP']:
   granules=earthaccess.search_data(short_name=product,bounding_box=(lon-.75,lat-.75,lon+.75,lat+.75),temporal=(start,end),count=max_granules)
   print(site.site_id,product,'overlapping daily granules:',len(granules))
   for g in granules:
    d=dict(g);meta=d.get('meta',{});umm=d.get('umm',{})
    rows.append({'site_id':site.site_id,'instrument':product,'granule_id':meta.get('native-id') or umm.get('GranuleUR',''),
      'status':'daily_granule_overlap_only_QA_soundings_not_yet_checked'})
   selected.extend(granules)
 pd.DataFrame(rows,columns=['site_id','instrument','granule_id','status']).to_csv(OUT/'oco_search.csv',index=False)
 if download and selected:
  earthaccess.login(strategy='interactive')
  cache=ROOT/'data/cache/oco_landfills';cache.mkdir(parents=True,exist_ok=True)
  files=earthaccess.download(selected,str(cache))
  lite=[Path(f) for f in files if str(f).lower().endswith(('.nc4','.nc','.h5'))]
  if lite:return import_oco(lite,site_filter)
 return pd.DataFrame(rows)

def import_oco(files,site_filter=None):
 """Summarize QA-good OCO-2/3 Lite XCO2 near site versus 25–80 km ring."""
 import h5py
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for file in map(Path,files):
  with h5py.File(file) as h:
   lat=np.asarray(h['latitude'][:]).ravel();lon=np.asarray(h['longitude'][:]).ravel()
   x=np.asarray(h['xco2'][:],dtype=float).ravel()
   qa=np.asarray(h['xco2_quality_flag'][:]).ravel()
  if not (lat.size==lon.size==x.size==qa.size):raise ValueError(f'Lite array length mismatch: {file}')
  valid=np.isfinite(lat)&np.isfinite(lon)&np.isfinite(x)&(x>300)&(x<600)&(qa==0)
  instrument='OCO-3' if 'oco3' in file.name.lower() else 'OCO-2' if 'oco2' in file.name.lower() else 'OCO Lite'
  for site in sites().itertuples():
   if site_filter and site.site_id!=site_filter:continue
   d=np.hypot((lat-float(site.latitude))*111.1,(lon-float(site.longitude))*111.1*math.cos(math.radians(float(site.latitude))))
   near=x[valid&(d<=25)];bg=x[valid&(d>25)&(d<=80)]
   good=len(near)>=3 and len(bg)>=3
   rows.append({'site_id':site.site_id,'site_name':site.name,'instrument':instrument,'file':file.name,
    'near_n':len(near),'background_n':len(bg),'near_xco2_ppm':float(np.median(near)) if len(near) else None,
    'background_xco2_ppm':float(np.median(bg)) if len(bg) else None,
    'near_minus_background_ppm':float(np.median(near)-np.median(bg)) if good else None,
    'status':'regional_column_contrast_not_source_attribution' if good else 'insufficient_QA_valid_coverage'})
 result=pd.DataFrame(rows,columns=OCO_COLUMNS)
 result.to_csv(OUT/'regional_xco2.csv',index=False)
 print('OCO Lite site-file summaries:',len(result),'QA-valid contrasts:',sum(result.status.eq('regional_column_contrast_not_source_attribution')))
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--site',choices=sites().site_id.tolist(),help='Limit to one landfill')
 parser.add_argument('--search-emit',action='store_true',help='Search NASA CMR for CH4 and CO2 V002 plume granules')
 parser.add_argument('--download',action='store_true',help='Earthdata login and download searched products')
 parser.add_argument('--search-oco',action='store_true',help='Search OCO-2/3 L2 Lite daily CO2 files')
 parser.add_argument('--emit-dir',type=Path,help='Process downloaded EMIT V002 plume GeoJSON directory')
 parser.add_argument('--oco',type=Path,nargs='+',help='Process downloaded OCO-2/3 L2 Lite NetCDF files')
 parser.add_argument('--start',default='2022-01-01');parser.add_argument('--end',default='2026-09-29')
 parser.add_argument('--max-granules',type=int,default=50)
 args=parser.parse_args()
 if not(args.search_emit or args.search_oco or args.emit_dir or args.oco):parser.error('choose --search-emit, --search-oco, --emit-dir, or --oco')
 if args.search_emit:search_emit(args.site,args.start,args.end,args.max_granules,args.download)
 if args.search_oco:search_oco(args.site,args.start,args.end,args.max_granules,args.download)
 if args.emit_dir:import_emit(args.emit_dir,args.site)
 if args.oco:import_oco(args.oco,args.site)
