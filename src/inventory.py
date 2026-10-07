"""Optional activity-based GHG calculation. User supplies all emission factors and sources."""
from pathlib import Path
import pandas as pd

REQUIRED=['facility_id','period','fuel_type','fuel_quantity','fuel_unit','fuel_factor_kgco2e_per_unit',
          'electricity_kwh','electricity_factor_kgco2e_per_kwh','factor_source','activity_source']

def calculate(path, allow_synthetic=False):
    frame=pd.read_csv(path)
    if not set(REQUIRED).issubset(frame.columns):
        raise ValueError('Missing inventory fields: '+', '.join(sorted(set(REQUIRED)-set(frame.columns))))
    if frame.empty:return pd.DataFrame()
    if frame.duplicated(['facility_id','period']).any():
        raise ValueError('Use one row per facility and period; aggregate fuel first to avoid double-counting electricity')
    for col in ['fuel_quantity','fuel_factor_kgco2e_per_unit','electricity_kwh','electricity_factor_kgco2e_per_kwh']:
        frame[col]=pd.to_numeric(frame[col],errors='raise')
        if (frame[col]<0).any():raise ValueError(col+' cannot be negative')
    for col in ['factor_source','activity_source']:
        if frame[col].isna().any() or frame[col].astype(str).str.strip().eq('').any():
            raise ValueError(col+' must identify documented evidence')
        if not allow_synthetic and frame[col].astype(str).str.contains('SYNTHETIC',case=False).any():
            raise ValueError('Synthetic activity or factors cannot be used in real-data mode')
    frame['scope1_tco2e']=frame.fuel_quantity*frame.fuel_factor_kgco2e_per_unit/1000
    frame['scope2_tco2e']=frame.electricity_kwh*frame.electricity_factor_kgco2e_per_kwh/1000
    frame['total_tco2e']=frame.scope1_tco2e+frame.scope2_tco2e
    return frame

if __name__=='__main__':
    import sys
    print(calculate(sys.argv[1] if len(sys.argv)>1 else 'data/facility_activity.csv').to_string(index=False))
