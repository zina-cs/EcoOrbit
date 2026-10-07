"""Create reporting-period Scope 1/2 CO2e output from documented activity records.

A satellite instantaneous CH4/CO2 plume is never annualized here.
"""
from pathlib import Path
import json
from src.inventory import calculate
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/real/carbon'
def run(path=None):
 source=Path(path) if path else ROOT/'data/facility_activity.csv'
 OUT.mkdir(parents=True,exist_ok=True)
 if not source.exists():
  status={'status':'awaiting_facility_activity_and_documented_factors','source_template':'data/facility_activity_template.csv',
  'interpretation':'No Scope 1/2 number is reported; satellite plume rates cannot establish annual inventory.'}
  (OUT/'status.json').write_text(json.dumps(status,indent=2));print(status['status']);return None
 frame=calculate(source)
 if frame.empty:raise ValueError('Activity CSV has no rows; do not report zero emissions from missing records')
 result=frame[['facility_id','period','scope1_tco2e','scope2_tco2e','total_tco2e','factor_source','activity_source']]
 result.to_csv(OUT/'scope1_scope2_by_period.csv',index=False)
 (OUT/'status.json').write_text(json.dumps({'status':'calculated_from_supplied_activity','row_count':len(result),
  'units':'metric tonnes CO2e by declared reporting period','source_file':str(source)},indent=2))
 print(result.to_string(index=False));return result
if __name__=='__main__':
 import sys
 run(sys.argv[1] if len(sys.argv)>1 else None)
