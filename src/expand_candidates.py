"""Build an unverified expansion list from saved EPA FRS TRI query responses.

No candidate becomes a training label until its scene pixel is QA checked,
operating status and site geometry are checked, and spectra are extracted.
"""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
BOXES={'Jacksonville':(-81.69369938031545,30.259070621905575,-81.45079750932877,30.439677039738726),
'Rochester':(-77.7151722184759,43.06303136820783,-77.40833399105284,43.259199834613476),
'Detroit':(-83.33175247670914,42.14831477016702,-83.01418472462309,42.40408910830337)}
SNAP={'Jacksonville':'frs_30.35.json','Rochester':'frs_43.15.json','Detroit':'frs_42.28.json'}
def run():
 used=set(pd.read_csv(ROOT/'data/training_sites.csv',dtype={'facility_id':str}).facility_id)
 rows=[]
 for city,bbox in BOXES.items():
  records=json.loads((ROOT/'data/source_snapshots'/SNAP[city]).read_text())['Results']['FRSFacility']
  for r in records:
   try:lat=float(r['Latitude83']);lon=float(r['Longitude83'])
   except (TypeError,ValueError,KeyError):continue
   if not (bbox[0]+.002<lon<bbox[2]-.002 and bbox[1]+.002<lat<bbox[3]-.002):continue
   fid=str(r['RegistryId'])
   if fid in used:continue
   rows.append({'facility_id':fid,'name':r['FacilityName'],'city':city,'latitude':lat,'longitude':lon,
    'status':'candidate_only_needs_image_QA_geometry_and_operating_check',
    'source_url':f'https://frs-public.epa.gov/ords/frs_public2/fii_query_dtl.disp_program_facility?p_registry_id={fid}'})
 df=pd.DataFrame(rows).drop_duplicates('facility_id').sort_values(['city','name'])
 df.to_csv(ROOT/'data/candidate_factories.csv',index=False)
 print(df.groupby('city').size().to_string(), '\nTotal candidate sites:',len(df))
if __name__=='__main__':run()
