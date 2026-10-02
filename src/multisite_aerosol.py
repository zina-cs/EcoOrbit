"""Satellite AOT screening across three US pilot cities; regional context only."""
from pathlib import Path
import pandas as pd,matplotlib.pyplot as plt
from aerosol import scenes,scene_facility
from wind import fetch_wind,closest_wind
DATES={'Jacksonville':'2025-05-13/2025-05-25','Rochester':'2025-07-30/2025-08-10','Detroit':'2025-09-11/2025-09-23'}

def analyze(registry='data/training_sites.csv',out='results/real/aot'):
 sites=pd.read_csv(registry);sites=sites[sites.label.eq(1)]
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 rows=[];provenance=[]
 for city,group in sites.groupby('city'):
  bbox=(group.longitude.min()-.04,group.latitude.min()-.04,group.longitude.max()+.04,group.latitude.max()+.04)
  try:
   options=scenes(bbox=bbox,dates=DATES[city]);options=sorted(options,key=lambda i:i.properties.get('eo:cloud_cover',100))
   if not options:raise RuntimeError('No Sentinel-2 scene')
   item=options[0]
   wind,_=fetch_wind(float(group.latitude.mean()),float(group.longitude.mean()),DATES[city].split('/')[0],DATES[city].split('/')[1])
   matched=closest_wind(wind,item.datetime)
   for _,site in group.iterrows():
    try:
     a=scene_facility(item,float(site.latitude),float(site.longitude),wind=matched)
     if a:rows.append({'city':city,'facility_id':site.facility_id,'name':site['name'],'date':item.datetime.date().isoformat(),'scene_id':item.id,**a})
    except Exception as e:print(city,site.facility_id,'AOT skipped:',type(e).__name__,str(e)[:80],flush=True)
   provenance.append({'city':city,'scene_id':item.id,'date':item.datetime.date().isoformat(),'tile_cloud_percent':item.properties.get('eo:cloud_cover'),'n_valid_facilities':sum(r['city']==city for r in rows)})
   print(city,'valid AOT',provenance[-1]['n_valid_facilities'],flush=True)
  except Exception as e:print(city,'no AOT:',type(e).__name__,str(e)[:150],flush=True)
 pd.DataFrame(provenance).to_csv(out/'multicity_scene_provenance.csv',index=False)
 df=pd.DataFrame(rows)
 if not df.empty:
  df.to_csv(out/'multicity_aot_comparison.csv',index=False)
  fig,ax=plt.subplots(figsize=(10,4))
  for city,g in df.groupby('city'):ax.scatter([city]*len(g),g.difference,label=city,alpha=.7)
  ax.axhline(0,color='black',lw=1);ax.set(ylabel='Near minus reference AOT (dimensionless)',title='Sentinel-2 550 nm aerosol screening across sites');fig.tight_layout();fig.savefig(out/'multicity_aot.png',dpi=150);plt.close(fig)
 return df
if __name__=='__main__':print(analyze().groupby('city').size())
