"""Sentinel-2 L2A aerosol optical thickness (AOT) around sourced facilities.
This is an aerosol screening comparison, NEVER a factory emissions determination.
"""
from pathlib import Path
import json
import numpy as np,pandas as pd,matplotlib.pyplot as plt,rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.transform import from_origin
from rasterio.warp import transform as transform_points
from pystac_client import Client
import planetary_computer as pc
from wind import fetch_wind, closest_wind

STAC='https://planetarycomputer.microsoft.com/api/stac/v1'

def scenes(bbox=(-81.68,30.31,-81.62,30.37), dates='2025-05-13/2025-05-25'):
    cat=Client.open(STAC)
    items=list(cat.search(collections=['sentinel-2-l2a'],bbox=bbox,datetime=dates,
                          query={'eo:cloud_cover':{'lt':30}},max_items=120).items())
    # One item per day, choosing lower tile cloud percentage; local SCL filter still applied.
    by_day={}
    for i in items:
        day=i.datetime.date().isoformat()
        if day not in by_day or i.properties.get('eo:cloud_cover',100)<by_day[day].properties.get('eo:cloud_cover',100):by_day[day]=i
    return [pc.sign(by_day[k]) for k in sorted(by_day)]

def value(asset,grid,shape,resampling,crs):
    with rasterio.open(asset.href) as src:
        with WarpedVRT(src,crs=crs,transform=grid,width=shape[1],height=shape[0],resampling=resampling) as vrt:
            return vrt.read(1).astype('float32')

def scene_facility(item,lat,lon,wind=None,near_m=500,inner_m=2000,outer_m=4000):
    if 'AOT' not in item.assets or 'SCL' not in item.assets: raise ValueError('Scene lacks AOT/SCL assets')
    zone=int((lon+180)//6)+1
    crs=f'EPSG:{32600+zone if lat>=0 else 32700+zone}'
    x,y=transform_points('EPSG:4326',crs,[lon],[lat]);x,y=x[0],y[0]
    res=20;half=outer_m+res;n=int(np.ceil(2*half/res)); grid=from_origin(x-half,y+half,res,res);shape=(n,n)
    raw=value(item.assets['AOT'],grid,shape,Resampling.nearest,crs)
    scl=value(item.assets['SCL'],grid,shape,Resampling.nearest,crs)
    meta=item.assets['AOT'].extra_fields.get('raster:bands',[{}])[0]
    scale=meta.get('scale',.001); offset=meta.get('offset',0)
    aot=raw*scale+offset
    yy,xx=np.mgrid[:n,:n]; dist=np.hypot((xx+.5)*res-half,half-(yy+.5)*res)
    valid=(raw>0)&np.isin(scl,[4,5,7])&np.isfinite(aot)&(aot>=0)&(aot<=3)
    near=valid&(dist<=near_m);ref=valid&(dist>=inner_m)&(dist<=outer_m)
    if near.sum()<20 or ref.sum()<100:return None
    result={'near_aot':float(np.median(aot[near])),'reference_aot':float(np.median(aot[ref])),
            'difference':float(np.median(aot[near])-np.median(aot[ref])),
            'near_pixels':int(near.sum()),'reference_pixels':int(ref.sum()),'aot_scale':scale}
    result.update(wind or {})
    result.update({'downwind_aot':np.nan,'upwind_aot':np.nan,'downwind_minus_upwind':np.nan,
                   'directional_status':'Wind unavailable or calm'})
    if wind and wind['wind_speed_kmh']>=2:
        # Bearing clockwise from north. Wind's reported bearing is where it comes FROM.
        bearing=(np.degrees(np.arctan2((xx+.5)*res-half,half-(yy+.5)*res))+360)%360
        toward=wind['wind_toward_deg']
        angular=lambda direction: abs((bearing-direction+180)%360-180)
        ring=valid&(dist>=near_m)&(dist<=inner_m)
        down=ring&(angular(toward)<=45)
        up=ring&(angular(wind['wind_from_deg'])<=45)
        if down.sum()>=20 and up.sum()>=20:
            result.update({'downwind_aot':float(np.median(aot[down])),
                           'upwind_aot':float(np.median(aot[up])),
                           'downwind_minus_upwind':float(np.median(aot[down])-np.median(aot[up])),
                           'directional_status':'Wind-sector aerosol contrast; not source attribution'})
        else: result['directional_status']='Insufficient valid upwind/downwind pixels'
    return result

def analyze(facilities='data/facilities.csv',out='results/aot'):
    df=pd.read_csv(facilities); df=df[df.kind.eq('manufacturing_site')].dropna(subset=['latitude','longitude'])
    if df.empty:raise ValueError('Provide at least one factory with checked latitude/longitude')
    items=scenes(); rows=[]
    if not items:raise RuntimeError('No Sentinel-2 scenes in requested date range')
    wind_data,wind_meta=fetch_wind()
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    wind_data.to_csv(out/'wind_hourly.csv',index=False)
    for item in items:
        wind=closest_wind(wind_data,item.datetime)
        for _,f in df.iterrows():
            try: stats=scene_facility(item,float(f.latitude),float(f.longitude),wind=wind)
            except Exception as ex:
                print('Skipped',item.id,f.facility_id,type(ex).__name__,str(ex)[:120]);continue
            if stats:rows.append({'facility_id':f.facility_id,'name':f['name'],'scene_id':item.id,
                                  'date':item.datetime.date().isoformat(),**stats})
    result=pd.DataFrame(rows)
    if result.empty:raise RuntimeError('No cloud-free valid near/reference comparisons; widen dates or inspect imagery')
    result.to_csv(out/'aot_comparison.csv',index=False)
    plot=result.assign(date=pd.to_datetime(result.date)).set_index('date')
    ax=plot[['difference','downwind_minus_upwind']].plot(marker='o',title='AOT screening contrasts (550 nm)')
    ax.axhline(0,color='black',lw=1)
    ax.set_ylabel('AOT contrast (dimensionless)');ax.figure.tight_layout();ax.figure.savefig(out/'aot_comparison.png',dpi=150);plt.close(ax.figure)
    (out/'interpretation.json').write_text(json.dumps({'status':'aerosol screening only; no factory attribution',
      'method':'500m circle median minus 2-4km annulus median, SCL cloud/water masked',
      'wind':wind_meta,
      'directional_method':'500m-2km upwind versus downwind 90-degree sectors; wind direction FROM north clockwise; 10m reanalysis wind nearest scene hour',
      'caveat':'AOT may be coarsely estimated or CAMS-filled; wind varies with height, nearby sites overlap, ground validation absent; no emission rate or attribution',
      'n_scenes':int(result.scene_id.nunique())},indent=2))
    return result
if __name__=='__main__':print(analyze().to_string(index=False))
