"""Deterministic synthetic fixture for offline smoke test; not observational evidence."""
import json
from pathlib import Path
import h5py,numpy as np,pandas as pd
out=Path('data/sample_input');out.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(813);h,w=72,80; wl=np.arange(450,2401,15)
y,x=np.mgrid[:h,:w]
category=np.where(x<12,0,np.where(y<20,1,np.where((x>35)&(y>25),2,3)))
spectra=[]
for k in range(4):
 base=.10+.03*np.sin(wl/340+k)+.04*k
 base+=np.where((wl>750)&(wl<1150),.21 if k==1 else 0,0)
 base+=np.where((wl>1500)&(wl<1800),.14 if k in (2,3) else 0,0)
 if k==0:base*=.45
 spectra.append(base)
arr=np.stack(spectra)[category].transpose(2,0,1).astype('float32')
arr+=rng.normal(0,.004,arr.shape).astype('float32')
root='HDFEOS/GRIDS/HYP/Data Fields'
with h5py.File(out/'example_tanager_like.h5','w') as f:
 g=f.require_group(root);g.create_dataset('surface_reflectance',data=arr,compression='gzip')
 for m in ['nodata_pixels','beta_cloud_mask','beta_cirrus_mask']:g.create_dataset(m,data=np.zeros((h,w),np.uint8))
item={'id':'SYNTHETIC_FIXTURE','bbox':[106.56597,10.58628,106.77947,10.77719],
 'properties':{'datetime':'2025-04-07T03:55:09Z','license':'CC-BY-4.0'},
 'assets':{'ortho_sr_hdf5':{'bands':[{'eo:center_wavelength':float(z/1000)} for z in wl]}}}
(out/'example_item.json').write_text(json.dumps(item))
t=pd.date_range('2026-09-01',periods=7*24,freq='h',tz='UTC');d=pd.DataFrame({'time':t})
for j,key in enumerate(['pm2_5','pm10','nitrogen_dioxide','sulphur_dioxide']):d[key]=10+j*6+3*np.sin(np.arange(len(t))/8+j)
d.to_csv(out/'example_air_SYNTHETIC.csv',index=False)
wind_t=pd.date_range('2025-03-15',periods=47*24,freq='h',tz='UTC')
wind=pd.DataFrame({'time':wind_t,'wind_speed_10m':8+2*np.sin(np.arange(len(wind_t))/13),
                   'wind_direction_10m':(225+20*np.sin(np.arange(len(wind_t))/37))%360})
wind.to_csv(out/'example_wind_SYNTHETIC.csv',index=False)
dates=pd.date_range('2025-03-15',periods=8,freq='5D')
aot=pd.DataFrame({'facility_id':['NIDEC001']*8,'date':dates.strftime('%Y-%m-%d'),
                  'near_aot':np.linspace(.18,.28,8),'reference_aot':np.linspace(.20,.24,8)})
aot['difference']=aot.near_aot-aot.reference_aot
aot['wind_speed_kmh']=[8,9,10,6,7,11,8,9]
aot['wind_from_deg']=[220,225,240,210,230,225,215,235]
aot['wind_toward_deg']=(aot.wind_from_deg+180)%360
aot['downwind_aot']=aot.near_aot+.01
aot['upwind_aot']=aot.reference_aot-.005
aot['downwind_minus_upwind']=aot.downwind_aot-aot.upwind_aot
aot['directional_status']='SYNTHETIC example only'
aot.to_csv(out/'example_aot_SYNTHETIC.csv',index=False)
print('Created synthetic input fixture; no observed air, wind or imagery')
