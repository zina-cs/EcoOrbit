"""QA-filtered Landsat Collection 2 L2 surface-temperature site contrast."""
from pathlib import Path
import numpy as np,pandas as pd,rasterio,matplotlib.pyplot as plt
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.transform import from_origin
from rasterio.warp import transform
from pystac_client import Client
import planetary_computer as pc
WINDOWS={'Jacksonville':'2025-05-01/2025-06-20','Rochester':'2025-07-15/2025-09-15','Detroit':'2025-08-25/2025-10-20'}
def read(asset,grid,n,crs):
 with rasterio.open(asset.href) as src:
  with WarpedVRT(src,crs=crs,transform=grid,width=n,height=n,resampling=Resampling.nearest) as v:return v.read(1)
def site(item,s):
 lat,lon=float(s.latitude),float(s.longitude);crs=f'EPSG:{32600+int((lon+180)//6)+1}';x,y=transform('EPSG:4326',crs,[lon],[lat]);x,y=x[0],y[0]
 n=82;res=30;half=n*res/2;grid=from_origin(x-half,y+half,res,res)
 raw=read(item.assets['lwir11'],grid,n,crs);qa=read(item.assets['qa_pixel'],grid,n,crs).astype('uint16')
 meta=item.assets['lwir11'].extra_fields.get('raster:bands',[{}])[0];scale=float(meta.get('scale',.00341802));offset=float(meta.get('offset',149))
 if not np.isclose(scale,.00341802,rtol=.001) or not np.isclose(offset,149,atol=.1):raise ValueError('Unexpected Landsat ST scaling')
 valid=(raw>0)&(raw<65535)&((qa&((1<<0)|(1<<1)|(1<<2)|(1<<3)|(1<<4)|(1<<5)|(1<<7)))==0)
 yy,xx=np.indices((n,n));dist=np.hypot((xx+.5)*res-half,half-(yy+.5)*res);near=valid&(dist<=180);ref=valid&(dist>=600)&(dist<=1200)
 if near.sum()<10 or ref.sum()<100:return None
 temp=raw.astype('float32')*scale+offset-273.15
 return dict(surface_c=float(np.median(temp[near])),reference_c=float(np.median(temp[ref])),surface_excess_c=float(np.median(temp[near])-np.median(temp[ref])),near_pixels=int(near.sum()),reference_pixels=int(ref.sum()),scale=scale,offset_kelvin=offset)
def analyze(registry='data/training_sites.csv',out='results/real/heat',max_scenes=2):
 df=pd.read_csv(registry,dtype={'facility_id':str});df=df[df.label.eq(1)];out=Path(out);out.mkdir(parents=True,exist_ok=True);cat=Client.open('https://planetarycomputer.microsoft.com/api/stac/v1');rows=[];coverage=[]
 for city,g in df.groupby('city'):
  bbox=[g.longitude.min()-.02,g.latitude.min()-.02,g.longitude.max()+.02,g.latitude.max()+.02]
  items=list(cat.search(collections=['landsat-c2-l2'],bbox=bbox,datetime=WINDOWS[city],query={'eo:cloud_cover':{'lt':35}},max_items=100).items())
  items=sorted((i for i in items if {'lwir11','qa_pixel'}<=i.assets.keys()),key=lambda i:i.properties.get('eo:cloud_cover',100))
  days=set()
  for item in items:
   day=item.datetime.date().isoformat()
   if day in days:continue
   days.add(day);signed=pc.sign(item);n=0
   for _,s in g.iterrows():
    try:result=site(signed,s)
    except Exception as e:print('heat skip',city,s.facility_id,str(e)[:80],flush=True);continue
    if result:rows.append(dict(city=city,facility_id=s.facility_id,name=s['name'],date=day,scene_id=item.id,cloud_cover_scene=item.properties.get('eo:cloud_cover'),**result));n+=1
   coverage.append(dict(city=city,date=day,scene_id=item.id,valid_sites=n,total_sites=len(g)))
   pd.DataFrame(coverage).to_csv(out/'scene_coverage.csv',index=False)
   if rows:pd.DataFrame(rows).to_csv(out/'site_heat.csv',index=False)
   print('heat',city,day,n,flush=True)
   if len(days)>=max_scenes:break
 result=pd.DataFrame(rows)
 if not result.empty:
  fig,ax=plt.subplots(figsize=(9,4));result.boxplot(column='surface_excess_c',by='city',ax=ax);fig.suptitle('');ax.set(title='Site minus nearby land surface temperature',ylabel='°C');fig.tight_layout();fig.savefig(out/'site_heat.png',dpi=150);plt.close(fig)
 return result
if __name__=='__main__':print(analyze().groupby('city').size())
