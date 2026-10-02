"""Build a reproducible, weakly labeled US pilot register from EPA FRS and OSM."""
import csv,json,math,re
from pathlib import Path
import h5py,numpy as np
from rasterio.warp import transform
CACHE=Path('data/cache');SOURCES=Path('data/source_snapshots');OUT=Path('data/training_sites.csv')
SCENES={'Jacksonville':('FL','30.35','20250516_164837_16_4001'),
 'Rochester':('NY','43.15','20250801_165548_86_4001'),
 'Detroit':('MI','42.28','20250914_171527_18_4001')}
SELECT={
 'Jacksonville':['110001736998','110002102634','110000361938','110039071660','110000361965','110000759527','110000361885','110070790439'],
 'Rochester':['110000492173','110000774895','110009479466','110009465293','110000328155','110000848673','110001134843','110039496774'],
 'Detroit':['110050297717','110060497001','110000494019','110000407202','110000406622','110008058369','110001841552','110000614470']}
def distance_m(a,b):
 lat1,lon1=a;lat2,lon2=b;dlat=math.radians(lat2-lat1);dlon=math.radians(lon2-lon1)
 h=math.sin(dlat/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
 return 12742000*math.asin(min(1,math.sqrt(h)))
def main():
 rows=[]
 for city,(state,tag,scene) in SCENES.items():
  frs={x['RegistryId']:x for x in json.loads((SOURCES/f'frs_{tag}.json').read_text())['Results']['FRSFacility']}
  osm=json.loads((SOURCES/f'osm_schools_{city.lower()}.json').read_text())
  with h5py.File(CACHE/f'{scene}_ortho_sr.h5') as h:
   t=h['HDFEOS INFORMATION/StructMetadata.0'][()].decode();origin=re.search(r'UpperLeftPointMtrs=\(([-\d.]+),([-\d.]+)\)',t)
   x0,y0=map(float,origin.groups());epsg=int(h['HDFEOS/GRIDS/HYP'].attrs['epsg_code']);v=h['HDFEOS/GRIDS/HYP/Data Fields']
   good=(v['nodata_pixels'][:]==0)&(v['beta_cloud_mask'][:]==0)&(v['beta_cirrus_mask'][:]==0)
   def qa(lat,lon):
    x,y=transform('EPSG:4326',f'EPSG:{epsg}',[lon],[lat]);r=int((y0-y[0])/30);c=int((x[0]-x0)/30)
    if not (6<=r<good.shape[0]-6 and 6<=c<good.shape[1]-6):return 0
    return float(good[r-5:r+6,c-5:c+6].mean()) if good[r,c] else 0
   positives=[]
   for id in SELECT[city]:
    a=frs[id];lat=float(a['Latitude83']);lon=float(a['Longitude83']);quality=qa(lat,lon)
    if quality<.5:raise ValueError(f'{city} {id} insufficient clear pixels')
    positives.append((lat,lon))
    rows.append({'facility_id':id,'name':a['FacilityName'],'city':city,'state':state,'latitude':lat,'longitude':lon,'label':1,'site_type':'EPA TRI industrial facility','scene_id':scene,'valid_fraction_150m':quality,'source_url':f'https://frs-public.epa.gov/ords/frs_public2/fii_query_dtl.disp_program_facility?p_registry_id={id}'})
   controls=[]
   for a in osm:
    if len(controls)==8:break
    if a.get('class')!='amenity' or a.get('type') not in ('school','college','university'):continue
    if not a.get('display_name','').endswith('United States'):continue
    lat=float(a['lat']);lon=float(a['lon']);quality=qa(lat,lon)
    if quality<.5 or any(distance_m((lat,lon),p)<650 for p in positives+controls):continue
    controls.append((lat,lon))
    rows.append({'facility_id':f'OSM_{a["osm_type"]}_{a["osm_id"]}','name':a.get('name') or a['display_name'].split(',')[0],'city':city,'state':state,'latitude':lat,'longitude':lon,'label':0,'site_type':'OSM school comparison','scene_id':scene,'valid_fraction_150m':quality,'source_url':f'https://www.openstreetmap.org/{a["osm_type"]}/{a["osm_id"]}'})
   if len(controls)!=8:raise ValueError(f'{city}: only {len(controls)} clear school comparison sites')
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
 print('Saved',OUT,'sites',len(rows),'factories',sum(r['label'] for r in rows))
if __name__=='__main__':main()
