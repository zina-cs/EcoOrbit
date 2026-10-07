"""EcoOrbit research screening: Tanager hyperspectral surface + CAMS regional air context."""
import json, hashlib
from pathlib import Path
import numpy as np, pandas as pd, h5py, requests
import matplotlib.pyplot as plt
import re
from rasterio.warp import transform as transform_points
from sklearn.cluster import MiniBatchKMeans

SCENE='20250516_164837_16_4001'
STAC=f'https://www.planet.com/data/stac/tanager-core-imagery/urban/{SCENE}/{SCENE}.json'
PUBLIC_HDF5=f'https://storage.googleapis.com/open-cogs/planet-stac/tanager1-release2-core-imagery/ortho_sr_hdf5/{SCENE}_ortho_sr_hdf5.h5'
REFERENCE_BBOX=[-81.69369938031545,30.259070621905575,-81.45079750932877,30.439677039738726]
ROOT='HDFEOS/GRIDS/HYP/Data Fields'
AIR_URL='https://air-quality-api.open-meteo.com/v1/air-quality'
AIR_VARS=['nitrogen_dioxide','sulphur_dioxide']

def download(cache='data/cache'):
    cache=Path(cache); cache.mkdir(parents=True,exist_ok=True)
    item_path=cache/f'{SCENE}.json'
    if not item_path.exists():
        try:
            r=requests.get(STAC,timeout=15); r.raise_for_status(); item_path.write_text(r.text)
        except requests.RequestException:
            # The provider STAC host can be unreachable while its public HDF5 remains available.
            # Date, bounds and asset URL are reproduced from the supplied organizer notebook.
            item_path.write_text(json.dumps({'id':SCENE,'bbox':REFERENCE_BBOX,
              'properties':{'datetime':'2025-05-16T16:48:37.165094Z','license':'CC-BY-4.0'},
              'assets':{'ortho_sr_hdf5':{'href':PUBLIC_HDF5}},
              'metadata_provenance':'Organizer notebook 02_land_use_land_cover_change.ipynb; wavelengths from HDF5 attributes'},indent=2))
    item=json.loads(item_path.read_text()); assert item['id']==SCENE
    assert 'ortho_sr_hdf5' in item['assets'], 'This scene needs orthorectified SR HDF5'
    asset=item['assets']['ortho_sr_hdf5']; path=cache/f'{SCENE}_ortho_sr.h5'
    if not path.exists():
        temp=path.with_suffix('.part')
        with requests.get(asset['href'],stream=True,timeout=120) as r:
            r.raise_for_status()
            with open(temp,'wb') as f:
                for chunk in r.iter_content(1024*1024):
                    if chunk: f.write(chunk)
        temp.replace(path)
    return item,path

def wavelength_nm(item,n):
    bands=item['assets']['ortho_sr_hdf5'].get('bands',[])
    wl=np.array([b['eo:center_wavelength']*1000 for b in bands if 'eo:center_wavelength' in b])
    if len(wl)!=n: raise ValueError(f'STAC spectral bands {len(wl)} != cube bands {n}; inspect product metadata')
    return wl

def wavelengths_from_hdf5(sr,n):
    """The HDF5 stores measured scene wavelengths in nm; no STAC dependency."""
    raw=sr.attrs['wavelengths']
    wl=np.asarray(raw,dtype=float).ravel() if not isinstance(raw,str) else np.fromstring(raw.strip('[]'),sep=' ')
    if len(wl)!=n:raise ValueError(f'HDF5 wavelengths {len(wl)} != {n} bands')
    return wl

def make_features(item,path,bin_width=30,stride=2):
    """Select 30 nm mean reflectance bins; spatially subsample 2x; mask quality layers."""
    with h5py.File(path) as h:
        sr=h[f'{ROOT}/surface_reflectance']; n,height,width=sr.shape
        wl=wavelengths_from_hdf5(sr,n)
        mask=(h[f'{ROOT}/nodata_pixels'][::stride,::stride]==0)
        mask &= h[f'{ROOT}/beta_cloud_mask'][::stride,::stride]==0
        mask &= h[f'{ROOT}/beta_cirrus_mask'][::stride,::stride]==0
        centers=[]; layers=[]
        for start in range(450,2400,bin_width):
            center=start+bin_width/2
            if 1350<=center<=1450 or 1800<=center<=1950: continue
            ids=np.flatnonzero((wl>=start)&(wl<start+bin_width))
            if not len(ids): continue
            block=np.stack([sr[int(i),::stride,::stride] for i in ids]).astype('float32')
            block[(block<0)|(block>1.5)]=np.nan
            layers.append(np.nanmean(block,axis=0)); centers.append(float(np.mean(wl[ids])))
    cube=np.stack(layers,axis=-1)
    mask &= np.isfinite(cube).all(axis=-1)
    mask &= np.nanmean(cube,axis=-1)>0.01
    if mask.sum()<100: raise ValueError('Too few valid pixels; review masks and scale')
    return cube,np.array(centers),mask

def index(cube,centers,nm):
    j=int(np.argmin(abs(centers-nm)))
    if abs(centers[j]-nm)>35: raise ValueError(f'No suitable wavelength near {nm} nm')
    return cube[...,j]

def classify(cube,centers,mask,k=7):
    """Unsupervised hyperspectral material groups; semantic names are provisional."""
    rng=np.random.default_rng(813); pix=cube[mask]
    sample=pix[rng.choice(len(pix),min(20000,len(pix)),replace=False)]
    model=MiniBatchKMeans(n_clusters=k,random_state=813,batch_size=2048,n_init=5)
    model.fit(sample)
    ids=np.full(mask.shape,-1,np.int16); ids[mask]=model.predict(pix)
    def nd(a,b): return (a-b)/(a+b+1e-6)
    red,nir,green,swir=[index(cube,centers,x) for x in (665,850,560,1650)]
    ndvi,ndbi,mndwi=nd(nir,red),nd(swir,nir),nd(green,swir)
    names={}; table=[]
    for i in range(k):
        m=ids==i
        if not m.any(): continue
        a,b,c=[float(np.nanmedian(v[m])) for v in [ndvi,ndbi,mndwi]]
        name='water-like' if c>.10 else 'vegetation-like' if a>.25 else 'built/bare candidate'
        names[i]=name
        table.append({'cluster':i,'name':name,'pixels':int(m.sum()),'ndvi':a,'ndbi':b,'mndwi':c})
    return ids,pd.DataFrame(table),names,model

def air_context(bbox,start='2025-05-16',end='2025-05-22',cache='data/cache'):
    """CAMS global regional model via Open-Meteo, overlapping the image date."""
    cache=Path(cache); cache.mkdir(parents=True,exist_ok=True)
    lat=(bbox[1]+bbox[3])/2; lon=(bbox[0]+bbox[2])/2
    params={'latitude':round(lat,5),'longitude':round(lon,5),'hourly':','.join(AIR_VARS),
            'start_date':start,'end_date':end,'timezone':'UTC','domains':'cams_global'}
    key=hashlib.sha256(json.dumps(params,sort_keys=True).encode()).hexdigest()[:12]
    path=cache/f'air_{key}.json'
    if not path.exists():
        r=requests.get(AIR_URL,params=params,timeout=90); r.raise_for_status(); path.write_text(r.text)
    payload=json.loads(path.read_text())
    if payload.get('error'): raise ValueError('Air API: '+payload.get('reason','unknown'))
    df=pd.DataFrame(payload['hourly']); df['time']=pd.to_datetime(df['time'],utc=True)
    for v in AIR_VARS: df[v]=pd.to_numeric(df[v],errors='coerce')
    return df,{'request':params,'returned_latitude':payload.get('latitude'),'returned_longitude':payload.get('longitude'),'units':payload.get('hourly_units',{}),'source':'CAMS global model via Open-Meteo, regional context'}

def run(item,path,air=None,air_meta=None,out='results',stride=2):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    cube,centers,mask=make_features(item,path,stride=stride)
    ids,table,names,model=classify(cube,centers,mask)
    table.to_csv(out/'spectral_clusters.csv',index=False)
    pd.DataFrame(model.cluster_centers_.T,index=centers).rename_axis('wavelength_nm').to_csv(out/'cluster_spectra.csv')
    np.savez_compressed(out/'classified_sample.npz',cluster=ids,wavelength_nm=centers,valid=mask)
    # Report spectral context near geocoded facilities; do not relabel it as factory detection.
    facilities_file=Path('data/facilities.csv')
    site_markers=[]
    if facilities_file.exists():
        with h5py.File(path) as h:
            struct=h['HDFEOS INFORMATION/StructMetadata.0'][()].decode()
            origin=re.search(r'UpperLeftPointMtrs=\(([-\d.]+),([-\d.]+)\)',struct)
            epsg=int(h['HDFEOS/GRIDS/HYP'].attrs['epsg_code'])
        if origin:
            x0,y0=map(float,origin.groups())
            sites=pd.read_csv(facilities_file).dropna(subset=['latitude','longitude'])
            nearby=[]
            for _,site in sites.iterrows():
                x,y=transform_points('EPSG:4326',f'EPSG:{epsg}',[float(site.longitude)],[float(site.latitude)])
                col=int((x[0]-x0)/(30*stride));row=int((y0-y[0])/(30*stride))
                rad=max(1,int(150/(30*stride)))
                patch=ids[max(0,row-rad):row+rad+1,max(0,col-rad):col+rad+1]
                count=int((patch>=0).sum()) if 0<=row<ids.shape[0] and 0<=col<ids.shape[1] else 0
                counts=np.bincount(patch[patch>=0],minlength=len(model.cluster_centers_)) if count else np.zeros(len(model.cluster_centers_),int)
                exact=int(ids[row,col]) if 0<=row<ids.shape[0] and 0<=col<ids.shape[1] else -1
                full_row=int((y0-y[0])/30);full_col=int((x[0]-x0)/30)
                with h5py.File(path) as h:
                    flags=[h[f'{ROOT}/{layer}'][full_row,full_col] for layer in
                           ('nodata_pixels','beta_cloud_mask','beta_cirrus_mask')]
                source_valid=all(flag==0 for flag in flags)
                if source_valid:site_markers.append((col,row,str(site.facility_id)))
                nearby.append({'facility_id':site.facility_id,'name':site['name'],'scene_id':SCENE,
                  'source_pixel_valid':bool(source_valid),
                  'exact_sampled_pixel_valid':bool(exact>=0),
                  'valid_pixels_near_point':count,'dominant_spectral_cluster':int(counts.argmax()) if count else None,
                  'dominant_fraction':float(counts.max()/count) if count else None,
                  'interpretation':'150 m neighborhood material context; factory class unverified'})
            pd.DataFrame(nearby).to_csv(out/'facility_spectral_context.csv',index=False)
    fig,ax=plt.subplots(1,2,figsize=(12,4))
    ax[0].imshow(np.ma.masked_where(ids<0,ids),cmap='tab10',vmin=0,vmax=9)
    for col,row,label in site_markers:
        ax[0].scatter([col],[row],marker='x',s=65,color='red',linewidths=2)
        ax[0].annotate(label,(col,row),xytext=(5,-8),textcoords='offset points',fontsize=7,color='red',weight='bold')
    ax[0].set_title('Tanager spectral clusters + sourced factory points');ax[0].axis('off')
    for j in range(len(model.cluster_centers_)):ax[1].plot(centers,model.cluster_centers_[j],label=f'cluster {j}')
    ax[1].set(xlabel='Wavelength (nm)',ylabel='Surface reflectance',title='Binned cluster spectra');ax[1].legend(fontsize=7,ncol=2)
    fig.tight_layout();fig.savefig(out/'hyperspectral_classification.png',dpi=150);plt.close(fig)
    if air is not None:
        air.to_csv(out/'regional_air_context.csv',index=False)
        summary=[]
        for v in AIR_VARS:
            series=air[v].dropna()
            summary.append({'variable':v,'mean_ug_m3':float(series.mean()) if len(series) else None,
                            'p95_ug_m3':float(series.quantile(.95)) if len(series) else None,
                            'max_ug_m3':float(series.max()) if len(series) else None,
                            'n_hours':int(len(series)),
                            'status':'Regional model context; not facility emission'})
        pd.DataFrame(summary).to_csv(out/'air_summary.csv',index=False)
        daily=air.set_index('time')[AIR_VARS].resample('D').mean()
        fig,ax=plt.subplots(figsize=(10,4));daily.plot(ax=ax);ax.set(ylabel='Modelled concentration (µg/m³)',title='Regional CAMS model context, May 2025');fig.tight_layout();fig.savefig(out/'air_context.png',dpi=150);plt.close(fig)
    evidence={'scene_id':SCENE,'scene_datetime':item['properties']['datetime'],'bbox':item['bbox'],
       'hyperspectral_product':'Tanager orthorectified L2A surface reflectance','bin_nm':30,'stride':stride,
       'valid_pixels':int(mask.sum()),'clusters':table.to_dict(orient='records'),
       'air':air_meta,'limitations':['Clusters are unsupervised materials, not verified factory polygons','No independent classification accuracy yet','CAMS grid is regional model context; not source attribution','No measured emissions or UAE compliance finding']}
    (out/'evidence.json').write_text(json.dumps(evidence,indent=2,default=str))
    return evidence
