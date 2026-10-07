"""Extract source Tanager site spectra and retain legacy city-transfer check.

Use python -m src.evaluate_sites for the primary all-city site-level test.
EPA industrial registry and OSM school points are proxies, not verified parcel labels.
"""
import json,re
from pathlib import Path
import h5py,joblib,numpy as np,pandas as pd,matplotlib.pyplot as plt
from rasterio.warp import transform
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,accuracy_score,precision_score,recall_score,f1_score,confusion_matrix

ROOT='HDFEOS/GRIDS/HYP/Data Fields'
CACHE=Path('data/cache');OUT=Path('results/real/classifier')

def site_features(h,lat,lon):
 t=h['HDFEOS INFORMATION/StructMetadata.0'][()].decode()
 x0,y0=map(float,re.search(r'UpperLeftPointMtrs=\(([-\d.]+),([-\d.]+)\)',t).groups())
 epsg=int(h['HDFEOS/GRIDS/HYP'].attrs['epsg_code'])
 x,y=transform('EPSG:4326',f'EPSG:{epsg}',[lon],[lat])
 row=int((y0-y[0])/30);col=int((x[0]-x0)/30)
 sr=h[f'{ROOT}/surface_reflectance'];r=slice(row-5,row+6);c=slice(col-5,col+6)
 good=np.ones((11,11),bool)
 for key in ('nodata_pixels','beta_cloud_mask','beta_cirrus_mask'):good &= h[f'{ROOT}/{key}'][r,c]==0
 if not good[5,5] or good.sum()<50:raise ValueError('Site lacks enough valid source pixels')
 wl=np.asarray(sr.attrs['wavelengths'],dtype=float).ravel();features={}
 for start in range(450,2400,30):
  center=start+15
  if 1350<=center<=1450 or 1800<=center<=1950:continue
  ids=np.flatnonzero((wl>=start)&(wl<start+30))
  if not len(ids):continue
  block=sr[ids,r,c].astype('float32')
  block[(block<0)|(block>1.5)]=np.nan
  features[f'sr_{start}_{start+30}']=float(np.nanmedian(np.nanmean(block[:,good],axis=0)))
 def band(nm):
  band_idx=int(np.argmin(abs(wl-nm)))
  values=sr[band_idx,r,c].astype('float32')[good]
  values=values[(values>=0)&(values<=1.5)]
  return float(np.nanmedian(values)) if len(values) else np.nan
 green,red,nir,swir=[band(v) for v in (560,665,850,1650)]
 nd=lambda a,b:(a-b)/(a+b+1e-6)
 features.update(ndvi=nd(nir,red),ndbi=nd(swir,nir),mndwi=nd(green,swir))
 return features

def extract(registry='data/training_sites.csv'):
 sites=pd.read_csv(registry,dtype={'facility_id':str,'scene_id':str})
 rows=[]
 for scene,group in sites.groupby('scene_id'):
  with h5py.File(CACHE/f'{scene}_ortho_sr.h5') as h:
   for _,s in group.iterrows():
    f=site_features(h,float(s.latitude),float(s.longitude))
    rows.append({**s.to_dict(),**f})
 out=pd.DataFrame(rows)
 OUT.mkdir(parents=True,exist_ok=True)
 out.to_csv(OUT/'site_spectral_features.csv',index=False)
 return out

def model():
 return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),PCA(n_components=8,random_state=813),
                      LogisticRegression(C=0.1,class_weight='balanced',max_iter=2000,random_state=813))

def train():
 df=extract()
 cols=[c for c in df if c.startswith('sr_') or c in ('ndvi','ndbi','mndwi')]
 X=df[cols].to_numpy(dtype=float);y=df.label.to_numpy(int)
 results=[];metrics=[]
 for heldout in sorted(df.city.unique()):
  test=df.city.eq(heldout).to_numpy();m=model();m.fit(X[~test],y[~test]);prob=m.predict_proba(X[test])[:,1];pred=(prob>=.5).astype(int)
  for i,p,q in zip(np.flatnonzero(test),prob,pred):results.append({'facility_id':df.iloc[i].facility_id,'name':df.iloc[i]['name'],'city':heldout,'label':int(y[i]),'factory_screen_score':float(p),'predicted_label':int(q)})
  metrics.append({'held_out_city':heldout,'n_test':int(test.sum()),'auc':float(roc_auc_score(y[test],prob)),
   'accuracy':float(accuracy_score(y[test],pred)),'precision':float(precision_score(y[test],pred,zero_division=0)),
   'recall':float(recall_score(y[test],pred,zero_division=0)),'f1':float(f1_score(y[test],pred,zero_division=0))})
 pred_df=pd.DataFrame(results);metrics_df=pd.DataFrame(metrics)
 pred_df.to_csv(OUT/'heldout_site_predictions.csv',index=False)
 metrics_df.to_csv(OUT/'city_holdout_metrics.csv',index=False)
 final=model().fit(X,y);joblib.dump({'model':final,'features':cols,'label_scope':'EPA TRI-listed facilities vs OSM schools; not universal factory identification','scenes':sorted(df.scene_id.unique())},OUT/'factory_screen_model.joblib')
 factory=pred_df[pred_df.label.eq(1)].sort_values(['city','name'])
 factory.to_csv(OUT/'factory_screening_results.csv',index=False)
 fig,ax=plt.subplots(figsize=(8,4));ax.bar(metrics_df.held_out_city,metrics_df.auc,color='#1d7772');ax.axhline(.5,color='black',lw=1,ls='--');ax.set(ylim=(0,1),ylabel='Held-out city ROC AUC',title='Factory-versus-school spectral screen');fig.tight_layout();fig.savefig(OUT/'city_holdout_metrics.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(figsize=(10,5))
 for city,group in factory.groupby('city'):
  ax.scatter(group.longitude,group.latitude,s=35+group.factory_screen_score*85,label=f'{city} ({len(group)})',alpha=.8)
 ax.set(xlabel='Longitude',ylabel='Latitude',title='EPA industrial-site points: spectral screen score (marker size)')
 ax.legend();fig.tight_layout();fig.savefig(OUT/'factory_scores_map.png',dpi=150);plt.close(fig)
 summary={'n_industrial_sites':int(y.sum()),'n_school_controls':int((1-y).sum()),'n_cities':len(metrics_df),'feature_count':len(cols),
  'pooled_accuracy':float(accuracy_score(pred_df.label,pred_df.predicted_label)),
  'pooled_auc':float(roc_auc_score(pred_df.label,pred_df.factory_screen_score)),
  'pooled_confusion_matrix':confusion_matrix(pred_df.label,pred_df.predicted_label).tolist(),
  'limitation':'Weak site labels; 150m context includes non-roof pixels; school-only negatives; city holdout tests cross-city transfer, not factory-wide parcel accuracy'}
 (OUT/'training_summary.json').write_text(json.dumps(summary,indent=2))
 print(metrics_df.to_string(index=False));print(summary)
 return summary
if __name__=='__main__':train()
