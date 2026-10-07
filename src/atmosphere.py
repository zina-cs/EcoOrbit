"""Coarse regional TROPOMI CH4 and UV aerosol-index tracking.

Never interpret a TROPOMI value as a factory emission. Reads QA-screened L2 NetCDF.
"""
import concurrent.futures,json,math,os,time
from pathlib import Path
import h5py,numpy as np,pandas as pd,requests
from pystac_client import Client
import planetary_computer as pc
STAC='https://planetarycomputer.microsoft.com/api/stac/v1'
PRODUCTS={'ch4':('methane_mixing_ratio_bias_corrected','ppb',.50),'aer-ai':('aerosol_index_354_388','dimensionless',.80)}
CENTERS={'Jacksonville':(30.34,-81.648),'Rochester':(43.15,-77.62),'Detroit':(42.29,-83.15)}
DATES={'Jacksonville':'2025-05-16/2025-05-25','Rochester':'2025-08-01/2025-08-09','Detroit':'2025-09-14/2025-09-22'}

def download_asset(url,path,workers=8):
 path=Path(path)
 path.parent.mkdir(parents=True,exist_ok=True)
 n=int(requests.head(url,timeout=60).headers['Content-Length']);span=math.ceil(n/workers)
 if path.exists() and path.stat().st_size==n:return path
 def part(i):
  start=i*span;end=min(n-1,(i+1)*span-1)
  if start>n-1:return None
  local=path.with_name(path.name+f'.{i}.part')
  if local.exists() and local.stat().st_size==end-start+1:return local
  for attempt in range(4):
   try:
    r=requests.get(url,headers={'Range':f'bytes={start}-{end}'},timeout=45);r.raise_for_status()
    if r.status_code!=206 or len(r.content)!=end-start+1:raise IOError('Incomplete range response')
    local.write_bytes(r.content);return local
   except Exception:
    if attempt==3:raise
    time.sleep(2)
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:parts=list(pool.map(part,range(workers)))
 tmp=path.with_suffix('.assembling')
 with tmp.open('wb') as out:
  for local in parts:
   if local is not None:
    with local.open('rb') as src:
     while block:=src.read(2**20):out.write(block)
    local.unlink()
 if tmp.stat().st_size!=n:raise IOError('Incomplete assembled NetCDF')
 tmp.replace(path);return path

def read_context(path,center,product,radius_km=30):
 field,unit,minqa=PRODUCTS[product]
 with h5py.File(path) as h:
  grp=h['PRODUCT'];lat=grp['latitude'][0];lon=grp['longitude'][0]
  qa=grp['qa_value'][0];scale=float(np.asarray(grp['qa_value'].attrs.get('scale_factor',1)).ravel()[0]);qa=qa*scale
  available=[k for k in grp.keys() if k.startswith('aerosol_index')] if product=='aer-ai' else []
  if field not in grp and available:field=available[0]
  values=grp[field][0]
  dist=np.hypot((lat-center[0])*111.1,(lon-center[1])*111.1*math.cos(math.radians(center[0])))
  finite=np.isfinite(values)&(values<1e30)
  region=(dist<=radius_km)&(qa>minqa)&finite
  if product=='ch4':region &= (values>1000)&(values<3000)
  nearest=float(np.min(dist[region])) if region.any() else None
  return {'n_valid':int(region.sum()),'median':float(np.median(values[region])) if region.any() else None,
   'p95':float(np.quantile(values[region],.95)) if region.any() else None,'unit':unit,
   'nearest_valid_km':nearest,'radius_km':radius_km,'qa_threshold':minqa,'variable':field,
   'status':'regional observation' if region.any() else 'no QA-valid observation near city'}

def track(city,product,max_days=4,out='results/real/atmosphere',cache='data/cache'):
 if city not in CENTERS or product not in PRODUCTS:raise ValueError('Unknown city/product')
 out=Path(out);out.mkdir(parents=True,exist_ok=True);cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
 center=CENTERS[city];bbox=[center[1]-.4,center[0]-.4,center[1]+.4,center[0]+.4]
 catalog=Client.open(STAC)
 items=list(catalog.search(collections=['sentinel-5p-l2-netcdf'],bbox=bbox,datetime=DATES[city],
  query={'s5p:product_name':{'eq':product}},max_items=100).items())
 by_day={}
 for item in items:
  date=item.datetime.date().isoformat()
  if date not in by_day:by_day[date]=item
 rows=[]
 for day,item in list(sorted(by_day.items()))[:max_days]:
  asset=pc.sign(item).assets[product]
  local=download_asset(asset.href,cache/f'{item.id}.nc')
  record=read_context(local,center,product,radius_km=50 if product=='ch4' else 30)
  rows.append({'city':city,'date':day,'product':product,'scene_id':item.id,**record})
  pd.DataFrame(rows).to_csv(out/f'{city.lower()}_{product.replace("-","_")}.csv',index=False)
  print(city,day,product,record['n_valid'],record['median'],flush=True)
 df=pd.DataFrame(rows)
 if df.empty:
  df=pd.DataFrame([{'city':city,'date':DATES[city],'product':product,'scene_id':'',
   'n_valid':0,'median':None,'p95':None,'unit':PRODUCTS[product][1],
   'nearest_valid_km':None,'radius_km':50 if product=='ch4' else 30,
   'qa_threshold':PRODUCTS[product][2],'variable':PRODUCTS[product][0],
   'status':'no product scenes in queried image-week window'}])
 df.to_csv(out/f'{city.lower()}_{product.replace("-","_")}.csv',index=False)
 return df
if __name__=='__main__':
 for city in CENTERS:
  for product in PRODUCTS:track(city,product)
