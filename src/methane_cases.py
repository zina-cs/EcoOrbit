"""Real Sentinel-5P CH4 XCH4 case study; regional screening, never source attribution.

Downloads QA-filtered L2 orbital NetCDF through Microsoft Planetary Computer.
No observation and no eligible scene are recorded explicitly, never as zero.
"""
import argparse,math
from pathlib import Path
import h5py,numpy as np,pandas as pd
from pystac_client import Client
import planetary_computer as pc
from src.atmosphere import download_asset,STAC
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/real/methane';CACHE=ROOT/'data/cache/methane'
def extract(path,lat0,lon0):
 with h5py.File(path) as h:
  grp=h['PRODUCT'];lat=np.asarray(grp['latitude'][0]);lon=np.asarray(grp['longitude'][0])
  raw=np.asarray(grp['qa_value'][0],dtype=float);scale=float(np.asarray(grp['qa_value'].attrs.get('scale_factor',1)).ravel()[0]);qa=raw*scale
  x=np.asarray(grp['methane_mixing_ratio_bias_corrected'][0],dtype=float)
  d=np.hypot((lat-lat0)*111.1,(lon-lon0)*111.1*math.cos(math.radians(lat0)))
  ok=np.isfinite(x)&(x>1000)&(x<3000)&np.isfinite(qa)&(qa>.5)
  near=ok&(d<=25);background=ok&(d>25)&(d<=80)
  # Distinct observations are TROPOMI pixels, not independent factories.
  def med(mask):return float(np.median(x[mask])) if mask.any() else None
  n=int(near.sum());b=int(background.sum());a=med(near);c=med(background)
  return {'near_n':n,'background_n':b,'near_xch4_ppb':a,'background_xch4_ppb':c,
   'near_minus_background_ppb':a-c if n>=3 and b>=3 else None,
   'nearest_valid_km':float(d[near].min()) if n else None,'qa_threshold':.5,
   'status':'regional_column_contrast_not_attribution' if n>=3 and b>=3 else 'insufficient_QA_valid_pixels'}
def run(site_filter=None,max_scenes=8):
 sites=pd.read_csv(ROOT/'data/methane_sites.csv').set_index('site_id');windows=pd.read_csv(ROOT/'data/methane_windows.csv')
 if site_filter:windows=windows[windows.site_id.eq(site_filter)]
 OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
 catalog=Client.open(STAC);rows=[]
 for w in windows.itertuples():
  site=sites.loc[w.site_id];lat=float(site.latitude);lon=float(site.longitude)
  bbox=[lon-.9,lat-.9,lon+.9,lat+.9]
  try:
   items=list(catalog.search(collections=['sentinel-5p-l2-netcdf'],bbox=bbox,
    datetime=f'{w.window_start}/{w.window_end}',query={'s5p:product_name':{'eq':'ch4'}},max_items=150).items())
   seen=set();chosen=[]
   for item in sorted(items,key=lambda x:x.datetime):
    day=item.datetime.date().isoformat()
    if day not in seen:seen.add(day);chosen.append(item)
   if not chosen:
    rows.append({'site_id':w.site_id,'window_start':w.window_start,'window_end':w.window_end,
     'scene_id':'','date':'','status':'no_catalog_scene_not_no_emission','date_basis':w.event_evidence});continue
   for item in chosen[:max_scenes]:
    day=item.datetime.date().isoformat();asset=pc.sign(item).assets.get('ch4')
    if asset is None:raise KeyError(f'{item.id} has no ch4 asset')
    local=download_asset(asset.href,CACHE/f'{item.id}.nc')
    result=extract(local,lat,lon)
    rows.append({'site_id':w.site_id,'window_start':w.window_start,'window_end':w.window_end,
     'date':day,'scene_id':item.id,'date_basis':w.event_evidence,**result})
  except Exception as error:
   rows.append({'site_id':w.site_id,'window_start':w.window_start,'window_end':w.window_end,
    'scene_id':'','date':'','status':'processing_error','error':f'{type(error).__name__}: {error}',
    'date_basis':w.event_evidence})
  pd.DataFrame(rows).to_csv(OUT/'regional_ch4.csv',index=False)
 print('Saved',OUT/'regional_ch4.csv','rows',len(rows))
 return pd.DataFrame(rows)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--site',choices=['stanford_arizona','hassi_rmel','jeddah_landfill']);parser.add_argument('--max-scenes',type=int,default=8)
 args=parser.parse_args();run(args.site,args.max_scenes)
