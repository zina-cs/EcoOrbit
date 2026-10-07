"""Analyze real EMIT V002 pixels. Simple-IME scenario is NOT an attributed rate.

Run: python -m src.emit_pixels
Input: data/real_emit/jeddah_20240609 (original named TIFFs + GeoJSON + ERA5 JSON).
NASA ATBD: https://github.com/emit-sds/emit-sds-tgp/blob/develop/docs/EMIT_L2B_TRACE_GAS_ATBD.md
"""
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import reproject, Resampling
from shapely.geometry import MultiPoint
from pyproj import Geod, Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
SUFFIX='002_20240609T050226_2416104_002.tif'

def run(directory=None,out=None):
 directory=Path(directory or ROOT/'data/real_emit/jeddah_20240609')
 out=Path(out or ROOT/'results/real/emit_pixels/jeddah_20240609');out.mkdir(parents=True,exist_ok=True)
 meta=json.loads((directory/'EMIT_L2B_CH4PLMMETA_002_20240609T050226_003220.json').read_text())
 feature=meta['features'][0];props=feature['properties'];arrays={};manifest=[]
 for name in ('CH4ENH','CH4UNCERT','CH4SENS'):
  path=directory/f'EMIT_L2B_{name}_{SUFFIX}'
  with rasterio.open(path) as ds:
   if arrays and (ds.shape!=shape or ds.transform!=transform or ds.crs!=crs):raise ValueError('Companion grids do not match')
   shape,transform,crs=ds.shape,ds.transform,ds.crs
   arrays[name]=ds.read(1,masked=True).filled(np.nan).astype(float)
   manifest.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'tags':ds.tags()})
 inside=geometry_mask([feature['geometry']],shape,transform,invert=True)
 raw,unc,sens=[arrays[k] for k in ('CH4ENH','CH4UNCERT','CH4SENS')]
 # NASA: ENH/SENS removes multiplicative bias; UNCERT already has sensitivity in its denominator.
 quality=np.isfinite(raw)&np.isfinite(unc)&np.isfinite(sens)&(unc>0)&(sens>=.5)&(sens<=2)
 corrected=np.divide(raw,sens,out=np.full(shape,np.nan),where=quality)
 background=quality&~inside
 if background.sum()<100:raise ValueError('Insufficient background pixels')
 baseline=float(np.median(corrected[background]));bg_sigma=float(1.4826*np.median(abs(corrected[background]-baseline)))
 delta=corrected-baseline
 yy,xx=np.indices(shape);lon=transform.c+(xx+.5)*transform.a;lat=transform.f+(yy+.5)*transform.e
 geod=Geod(ellps='WGS84');area=np.empty(shape[0])
 for r in range(shape[0]):
  l=transform.c;top=transform.f+r*transform.e
  area[r]=abs(geod.polygon_area_perimeter([l,l+transform.a,l+transform.a,l],[top,top,top+transform.e,top+transform.e])[0])
 areas=np.broadcast_to(area[:,None],shape)
 weather=json.loads((directory/'era5_weather.json').read_text());hour=weather['hourly'];i=hour['time'].index('2024-06-09T05:00')
 wind=float(hour['wind_speed_10m'][i]);direction=float(hour['wind_direction_10m'][i]);temperature=float(hour['temperature_2m'][i])+273.15;pressure=float(hour['surface_pressure'][i])*100
 # ppm*m -> kg/m2 via ideal gas law; local weather P/T are explicit approximations.
 conversion=1e-6*.016043*pressure/(8.314462618*temperature)
 transfer=Transformer.from_crs(crs,'EPSG:32637',always_xy=True)
 records=[];base_mask=None
 for threshold in (500,1000,1500):
  mask=quality&inside&(delta>=threshold)&(delta>=2*unc)
  if mask.sum()<3:continue
  x,y=transfer.transform(lon[mask],lat[mask]);hull=MultiPoint(np.column_stack([x,y])).convex_hull
  points=np.asarray(hull.exterior.coords) if hull.geom_type=='Polygon' else np.column_stack([x,y])
  fetch=float(np.sqrt(((points[:,None]-points[None,:])**2).sum(axis=2)).max())
  mass=delta[mask]*conversion*areas[mask];ime=float(mass.sum());mass_sigma=float(np.sqrt(((unc[mask]*conversion*areas[mask])**2).sum()))
  q=3600*wind*ime/fetch
  # Assumed wind-error floor; not a measured confidence interval. Ignore spatial noise covariance.
  wind_sigma=max(1.5,.5*wind);q_sigma=3600/fetch*np.hypot(wind*mass_sigma,ime*wind_sigma)
  records.append({'threshold_ppmm':threshold,'selected_pixels':int(mask.sum()),'area_m2':float(areas[mask].sum()),'integrated_excess_ch4_kg':ime,'sensor_only_mass_sigma_kg':mass_sigma,'fetch_m':fetch,'hypothetical_simple_ime_kg_h':q,'partial_sigma_kg_h':float(q_sigma)})
  if threshold==500:base_mask=mask
 if base_mask is None:raise ValueError('No primary mask')
 report={'site_id':'jeddah_landfill','observed_utc':props['UTC Time Observed'],'source_scene':props['DAAC Scene Names'][0],
  'status':'pixel_analysis_complete; facility_emission_rate_not_validated',
  'provider_rate_kg_h':None,'attributed_emission_rate_kg_h':None,
  'valid_quality_pixels':int(quality.sum()),'background_pixels':int(background.sum()),'background_median_ppmm':baseline,'background_robust_sigma_ppmm':bg_sigma,
  'max_raw_enhancement_ppmm':float(np.nanmax(raw[inside])),'max_corrected_enhancement_ppmm':float(np.nanmax(corrected[inside])),
  'sensitivity_min':.5,'sensitivity_max':2,'snr_min':2,'pressure_pa':pressure,'temperature_k':temperature,
  'wind_m_s':wind,'wind_from_deg':direction,'wind_toward_deg':(direction+180)%360,'wind_time_utc':hour['time'][i]+'Z',
  'wind_grid_lat':weather['latitude'],'wind_grid_lon':weather['longitude'],'wind_source':'ERA5 via Open-Meteo archive; nearest hour and returned grid point',
  'assumed_wind_sigma_m_s':max(1.5,.5*wind),'scenarios':records,
  'limitations':['Provider did not supply origin, wind or rate. Landfill boundary/source attribution unverified.',
  'Entire vetted plume-complex polygon analyzed; may be an extended or multi-source emission. Simple IME requires a single steady localized source and suitable wind.',
  'Scenario uses all selected components and farthest-pixel fetch; not NASA origin-seeded 1 km/200 m selection.',
  'Weather is coarse hourly ERA5; P/T approximate near-surface conditions. Pixel noise covariance and model/source/mask systematics are not in partial sigma.',
  'Sensitivity-screened and background-subtracted values are EcoOrbit processing of NASA retrievals, not a new radiance matched-filter retrieval.',
  'No annual emissions or CO2 inventory calculated.'], 'input_manifest':manifest}
 (out/'pixel_summary.json').write_text(json.dumps(report,indent=2,allow_nan=False))
 with (out/'emission_scenarios.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=records[0].keys());w.writeheader();w.writerows(records)
 idx=np.flatnonzero(base_mask);r,c=np.unravel_index(idx,shape)
 with (out/'selected_pixels.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['row','col','latitude','longitude','raw_ppmm','sensitivity','corrected_minus_background_ppmm','sensor_uncertainty_ppmm','area_m2','excess_ch4_kg'])
  for ri,ci in zip(r,c):w.writerow([int(ri),int(ci),lat[ri,ci],lon[ri,ci],raw[ri,ci],sens[ri,ci],delta[ri,ci],unc[ri,ci],areas[ri,ci],delta[ri,ci]*conversion*areas[ri,ci]])
 profile={'driver':'GTiff','height':shape[0],'width':shape[1],'count':1,'dtype':'uint8','crs':crs,'transform':transform,'compress':'deflate'}
 with rasterio.open(out/'analysis_mask.tif','w',**profile) as ds:ds.write(base_mask.astype('uint8'),1)
 extent=[lon.min(),lon.max(),lat.min(),lat.max()];fig,axes=plt.subplots(1,3,figsize=(14,6),constrained_layout=True)
 for ax,values,title,cmap,vmin,vmax in zip(axes,[np.where(quality,delta,np.nan),np.where(quality,unc,np.nan),base_mask.astype(float)],['CH4 enhancement / sensitivity − background','Sensor uncertainty (sensitivity-corrected)','Selected pixels: ≥500 ppm·m and SNR ≥2'],['inferno','viridis','Greens'],[0,0,0],[2500,float(np.nanpercentile(unc[quality],98)),1]):
  im=ax.imshow(values,extent=extent,origin='upper',cmap=cmap,vmin=vmin,vmax=vmax);coords=np.asarray(feature['geometry']['coordinates'][0]);ax.plot(coords[:,0],coords[:,1],color='cyan',lw=.7)
  ax.scatter([39.390260],[21.644194],marker='+',s=70,color='red',label='Approximate landfill point');ax.set(title=title,xlabel='Longitude',ylabel='Latitude');ax.set_aspect(1/np.cos(np.deg2rad(21.64)));fig.colorbar(im,ax=ax,shrink=.55,label='ppm·m' if ax is not axes[2] else '0 excluded / 1 selected')
 axes[0].legend(fontsize=7);fig.suptitle('Jeddah · NASA EMIT · 9 June 2024 05:02 UTC\nReal pixel analysis; source attribution and emission-rate validity pending',fontsize=13)
 fig.savefig(out/'pixel_analysis.png',dpi=160);plt.close(fig)
 print(json.dumps({k:v for k,v in report.items() if k not in ('input_manifest','limitations')},indent=2))
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();run(a.input,a.output)
