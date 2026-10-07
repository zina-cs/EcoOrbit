"""Process all three uploaded landfill observations using real NASA EMIT pixels.

Brazil PLM-only analysis does not invent uncertainty/sensitivity rasters. Jeddah
uses its full companion products via src.emit_pixels. Flux scenarios are not
validated facility rates and never enter an annual inventory.
"""
from pathlib import Path
import json,csv,hashlib
import numpy as np,rasterio
from rasterio.features import geometry_mask
from pyproj import Geod,Transformer
from shapely.geometry import MultiPoint
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def process_brazil(case):
 folder=ROOT/'data/real_emit'/case;out=ROOT/'results/real/emit_pixels'/case;out.mkdir(parents=True,exist_ok=True)
 metadata_path=next(folder.glob('*CH4PLMMETA*.json'));metadata=json.loads(metadata_path.read_text());feature=metadata['features'][0];p=feature['properties'];path=next(folder.glob('*CH4PLM_*.tif'))
 with rasterio.open(path) as ds:
  values=ds.read(1,masked=True).filled(np.nan).astype(float);transform=ds.transform;crs=ds.crs;profile=ds.profile
 inside=geometry_mask([feature['geometry']],values.shape,transform,invert=True)
 valid=np.isfinite(values)&inside
 yy,xx=np.indices(values.shape);lon=transform.c+(xx+.5)*transform.a;lat=transform.f+(yy+.5)*transform.e
 weather=json.loads((folder/'era5_weather.json').read_text());h=weather['hourly'];stamp=np.datetime64(p['UTC Time Observed'].replace('Z',''));times=np.array(h['time'],dtype='datetime64[s]');t=stamp.astype('datetime64[s]').astype(float)
 # Interpolate wind components rather than directions across the 0/360 boundary.
 speeds=np.asarray(h['wind_speed_10m']);directions=np.deg2rad(h['wind_direction_10m']);ts=times.astype(float)
 u=np.interp(t,ts,-speeds*np.sin(directions));v=np.interp(t,ts,-speeds*np.cos(directions));wind=float(np.hypot(u,v));direction=float(np.rad2deg(np.arctan2(-u,-v))%360)
 temperature=float(np.interp(t,ts,h['temperature_2m']))+273.15;pressure=float(np.interp(t,ts,h['surface_pressure']))*100
 g=Geod(ellps='WGS84');areas=np.empty(values.shape)
 for row in range(values.shape[0]):
  left=transform.c;top=transform.f+row*transform.e
  a=abs(g.polygon_area_perimeter([left,left+transform.a,left+transform.a,left],[top,top,top+transform.e,top+transform.e])[0]);areas[row,:]=a
 conversion=1e-6*.016043*pressure/(8.314462618*temperature)
 tr=Transformer.from_crs(crs,'EPSG:32723',always_xy=True)
 scenarios=[];selected=None
 for threshold in (500,1000,1500):
  mask=valid&(values>=threshold)
  if mask.sum()<3:continue
  x,y=tr.transform(lon[mask],lat[mask]);hull=MultiPoint(np.column_stack([x,y])).convex_hull;points=np.asarray(hull.exterior.coords) if hull.geom_type=='Polygon' else np.column_stack([x,y]);fetch=float(np.sqrt(((points[:,None]-points[None,:])**2).sum(axis=2)).max())
  mass=float((values[mask]*areas[mask]*conversion).sum());flux=3600*wind*mass/fetch
  scenarios.append({'threshold_ppmm':threshold,'selected_pixels':int(mask.sum()),'area_m2':float(areas[mask].sum()),'integrated_excess_ch4_kg':mass,'fetch_m':fetch,'hypothetical_simple_ime_kg_h':float(flux),'partial_sigma_kg_h':None})
  if threshold==500:selected=mask
 if selected is None:raise ValueError('No 500 ppm m mask')
 summary={'site_id':'seropedica_landfill','case_id':case,'observed_utc':p['UTC Time Observed'],'source_scene':p['DAAC Scene Names'][0],
 'status':'plume_pixel_analysis_complete; diagnostic_flux_only','processing_mode':'NASA plume enhancement; no sensitivity correction or SNR screen applied',
 'provider_rate_kg_h':None,'attributed_emission_rate_kg_h':None,'max_raw_enhancement_ppmm':float(values[valid].max()),'valid_plume_pixels':int(valid.sum()),
 'wind_m_s':wind,'wind_from_deg':direction,'wind_toward_deg':(direction+180)%360,'wind_time_utc':p['UTC Time Observed'],
 'wind_grid_lat':weather['latitude'],'wind_grid_lon':weather['longitude'],'wind_source':'ERA5 via Open-Meteo; adjacent hourly u/v interpolation',
 'temperature_k':temperature,'pressure_pa':pressure,'scenarios':scenarios,
 'limitations':['Brazil inputs are vetted plume TIFF/GeoJSON only. No sensor uncertainty or sensitivity correction is applied; no total error bar is inferred.',
 'PLM pixels have no surrounding-scene background estimate here; threshold sensitivity is reported.',
 'Whole-complex Simple IME is diagnostic, not source-validated. Single steady localized source, source origin and facility attribution have not been established.',
 'Coarse ERA5 surface wind, temperature and pressure approximate plume conditions. Full model, mask and atmospheric errors are unquantified.',
 'Do not annualize these snapshots or insert diagnostic flux into Scope 1.'],
 'input_manifest':[{'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},{'file':metadata_path.name,'sha256':hashlib.sha256(metadata_path.read_bytes()).hexdigest()}]}
 (out/'pixel_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
 with (out/'emission_scenarios.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=scenarios[0]);w.writeheader();w.writerows(scenarios)
 with (out/'selected_pixels.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['row','col','latitude','longitude','raw_ppmm','analysis_enhancement_ppmm','sensor_uncertainty_ppmm','area_m2','excess_ch4_kg'])
  for row,col in zip(*np.where(selected)):w.writerow([row,col,lat[row,col],lon[row,col],values[row,col],values[row,col],'',areas[row,col],values[row,col]*areas[row,col]*conversion])
 profile.update(count=1,dtype='uint8',nodata=None,compress='deflate')
 with rasterio.open(out/'analysis_mask.tif','w',**profile) as ds:ds.write(selected.astype('uint8'),1)
 extent=[lon.min(),lon.max(),lat.min(),lat.max()];fig,axes=plt.subplots(1,2,figsize=(11,6),constrained_layout=True)
 for ax,vals,title,cmap,vmax in zip(axes,[np.where(valid,values,np.nan),selected.astype(float)],['NASA methane enhancement','Selected pixels: enhancement ≥500 ppm·m'],['inferno','Greens'],[float(np.nanpercentile(values[valid],98)),1]):
  im=ax.imshow(vals,extent=extent,origin='upper',vmin=0,vmax=vmax,cmap=cmap);coords=np.asarray(feature['geometry']['coordinates'][0]);ax.plot(coords[:,0],coords[:,1],color='cyan',lw=.8);ax.scatter([-43.760558],[-22.795703],s=80,color='red',marker='+');ax.set(title=title,xlabel='Longitude',ylabel='Latitude');ax.set_aspect(1/np.cos(np.deg2rad(22.8)));fig.colorbar(im,ax=ax,shrink=.6,label='ppm·m' if ax is axes[0] else 'Selected mask')
 axes[0].text(.02,.98,f'ERA5 wind {wind:.2f} m/s, from {direction:.0f}°',transform=axes[0].transAxes,va='top',fontsize=9,bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'})
 fig.suptitle('Seropédica · '+p['UTC Time Observed']+'\nReal plume pixels; flux scenarios are not attributed facility emissions',fontsize=13);fig.savefig(out/'pixel_analysis.png',dpi=160);plt.close(fig)
 return summary

def run():
 from src.emit_pixels import run as jeddah
 summaries=[jeddah()]
 summaries[0]['case_id']='jeddah_20240609';summaries[0]['processing_mode']='Sensitivity correction, background subtraction, SNR≥2'
 for name in ('seropedica_20240305','seropedica_20240924'):summaries.append(process_brazil(name))
 out=ROOT/'results/real/emit_pixels';(out/'case_summaries.json').write_text(json.dumps(summaries,indent=2))
 rows=[{'case_id':s['case_id'],'observed_utc':s['observed_utc'],'processing_mode':s['processing_mode'],'peak_raw_ppmm':s['max_raw_enhancement_ppmm'],'wind_m_s':s['wind_m_s'],**s['scenarios'][0]} for s in summaries]
 with (out/'case_comparison.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
 print('Completed cases:',[(s['case_id'],s['max_raw_enhancement_ppmm'],s['scenarios'][0]['integrated_excess_ch4_kg']) for s in summaries]);return summaries
if __name__=='__main__':run()
