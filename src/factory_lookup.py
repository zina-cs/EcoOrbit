"""Optional unverified industrial-feature leads from OpenStreetMap (ODbL)."""
import json,requests
from pathlib import Path
from pipeline import download
item,_=download(); w,s,e,n=item['bbox']; bbox=f'{s},{w},{n},{e}'
query='[out:json][timeout:60];(way["landuse"="industrial"]('+bbox+');way["industrial"]('+bbox+');node["industrial"]('+bbox+'););out center tags;'
r=requests.post('https://overpass-api.de/api/interpreter',data={'data':query},timeout=90);r.raise_for_status()
rows=[]
for obj in r.json()['elements']:
 loc=obj.get('center',obj); t=obj.get('tags',{})
 rows.append({'osm_type':obj['type'],'osm_id':obj['id'],'name':t.get('name',''),
  'latitude':loc.get('lat'),'longitude':loc.get('lon'),'industrial_tag':t.get('industrial',''),
  'source':'OpenStreetMap/Overpass ODbL','verified':False})
out=Path('data/industrial_leads.csv');out.parent.mkdir(exist_ok=True)
import pandas as pd
pd.DataFrame(rows).to_csv(out,index=False)
print(len(rows),'unverified industrial leads saved to',out)
