"""Two-date Sentinel-2 NDVI and NDBI site screening with SCL cloud mask."""
from pathlib import Path
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import transform
from pystac_client import Client
import planetary_computer as pc
from src.aerosol import value,STAC
WINDOWS={'Jacksonville':('2025-02-01/2025-03-31','2025-05-01/2025-06-30'),'Rochester':('2025-05-01/2025-06-30','2025-08-01/2025-09-30'),'Detroit':('2025-06-01/2025-07-31','2025-09-01/2025-10-31')}
def site(item,s):
 lat,lon=float(s.latitude),float(s.longitude);crs=f'EPSG:{32600+int((lon+180)//6)+1}';x,y=transform('EPSG:4326',crs,[lon],[lat]);x,y=x[0],y[0]
 n=102;res=20;half=n*res/2;grid=from_origin(x-half,y+half,res,res)
 red,nir,swir,scl=[value(item.assets[b],grid,(n,n),Resampling.nearest,crs) for b in ['B04','B08','B11','SCL']]
 valid=(red>0)&(nir>0)&(swir>0)&np.isin(scl,[4,5,7]);yy,xx=np.indices((n,n));dist=np.hypot((xx+.5)*res-half,half-(yy+.5)*res)
 near=valid&(dist<=180);ref=valid&(dist>=500)&(dist<=1000)
 if near.sum()<15 or ref.sum()<80:return None
 ndvi=(nir-red)/(nir+red+1e-6);ndbi=(swir-nir)/(swir+nir+1e-6)
 return dict(ndvi_site=float(np.median(ndvi[near])),ndvi_reference=float(np.median(ndvi[ref])),ndbi_site=float(np.median(ndbi[near])),ndbi_reference=float(np.median(ndbi[ref])),near_pixels=int(near.sum()),reference_pixels=int(ref.sum()))
def analyze(registry='data/training_sites.csv',out='results/real/land'):
 sites=pd.read_csv(registry,dtype={'facility_id':str});sites=sites[sites.label.eq(1)];out=Path(out);out.mkdir(parents=True,exist_ok=True);cat=Client.open(STAC);rows=[];coverage=[]
 for city,g in sites.groupby('city'):
  bbox=[g.longitude.min()-.02,g.latitude.min()-.02,g.longitude.max()+.02,g.latitude.max()+.02]
  for period,window in [('earlier',WINDOWS[city][0]),('later',WINDOWS[city][1])]:
   items=list(cat.search(collections=['sentinel-2-l2a'],bbox=bbox,datetime=window,query={'eo:cloud_cover':{'lt':25}},max_items=100).items())
   items=sorted((i for i in items if {'B04','B08','B11','SCL'}<=i.assets.keys()),key=lambda i:i.properties.get('eo:cloud_cover',100))
   if not items:coverage.append(dict(city=city,period=period,status='no scene'));continue
   item=pc.sign(items[0]);n=0
   for _,s in g.iterrows():
    try:result=site(item,s)
    except Exception as e:print('land skip',city,s.facility_id,str(e)[:80],flush=True);continue
    if result:rows.append(dict(city=city,facility_id=s.facility_id,name=s['name'],period=period,date=item.datetime.date().isoformat(),scene_id=item.id,**result));n+=1
   coverage.append(dict(city=city,period=period,date=item.datetime.date().isoformat(),scene_id=item.id,valid_sites=n));pd.DataFrame(coverage).to_csv(out/'scene_coverage.csv',index=False)
   if rows:pd.DataFrame(rows).to_csv(out/'site_indices.csv',index=False)
   print('land',city,period,n,flush=True)
 df=pd.DataFrame(rows)
 if not df.empty:
  wide=df.pivot_table(index=['city','facility_id','name'],columns='period',values=['ndvi_site','ndbi_site','ndvi_reference','ndbi_reference'],aggfunc='first');wide.columns=['_'.join(c) for c in wide.columns];wide=wide.reset_index()
  for kind in ['ndvi','ndbi']:
   for suffix in ['site','reference']:
    a=f'{kind}_{suffix}_earlier';b=f'{kind}_{suffix}_later'
    if a in wide and b in wide:wide[f'{kind}_{suffix}_change']=wide[b]-wide[a]
  wide.to_csv(out/'site_change.csv',index=False)
  fig,ax=plt.subplots(figsize=(9,4))
  if 'ndvi_site_change' in wide:
   for city,g in wide.groupby('city'):ax.scatter([city]*len(g),g.ndvi_site_change,label=city)
  ax.axhline(0,color='black',lw=1);ax.set(title='Site NDVI change',ylabel='Later minus earlier NDVI');fig.tight_layout();fig.savefig(out/'site_change.png',dpi=150);plt.close(fig)
 return df
if __name__=='__main__':print(analyze().groupby('city').size())
