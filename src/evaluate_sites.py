"""Evaluate observed site spectra with a fixed, city-balanced site split.

The test partition is never used to select the model. New candidate sites are
excluded until source imagery QA and independent label checks are completed.
"""
import json
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/real/classifier'
FEATURES=OUT/'site_spectral_features.csv'

def estimator(components):
 return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),PCA(n_components=components,random_state=813),LogisticRegression(C=.1,class_weight='balanced',max_iter=2000,random_state=813))

def run(expanded=False):
 out=OUT/'expanded' if expanded else OUT
 out.mkdir(parents=True,exist_ok=True)
 feature_path=OUT/'site_spectral_features_expanded.csv' if expanded else FEATURES
 df=pd.read_csv(feature_path,dtype={'facility_id':str,'scene_id':str})
 cols=[c for c in df if c.startswith('sr_') or c in ('ndvi','ndbi','mndwi')]
 X=df[cols].to_numpy(float);y=df.label.to_numpy(int)
 strata=df.city.astype(str)+'_'+(df.site_type.astype(str) if expanded else df.label.astype(str))
 tr,te=train_test_split(np.arange(len(df)),test_size=.25,random_state=813,stratify=strata)
 cv=StratifiedKFold(3,shuffle=True,random_state=813)
 # Candidate settings are evaluated exclusively on the 36 training sites.
 scores={k:float(cross_val_score(estimator(k),X[tr],y[tr],cv=cv,scoring='accuracy').mean()) for k in (4,8,12)}
 best=max(scores,key=lambda k:(scores[k],k==8))
 m=estimator(best).fit(X[tr],y[tr]);prob=m.predict_proba(X[te])[:,1];prediction=(prob>=.5).astype(int)
 split=df[['facility_id','name','city','label','site_type']].copy();split['partition']='train';split.loc[te,'partition']='test';split.to_csv(out/'site_split.csv',index=False)
 observed=df.iloc[te][['facility_id','name','city','latitude','longitude','label','site_type']].copy()
 observed['factory_screen_score']=prob;observed['predicted_label']=prediction
 observed.to_csv(out/'all_city_test_predictions.csv',index=False)
 cm=confusion_matrix(y[te],prediction,labels=[0,1]).tolist()
 summary={'protocol':'Site-level 75/25 split stratified by city and label; fixed seed 813; train-only three-fold model selection',
          'n_train':len(tr),'n_test':len(te),'test_by_city_and_class':observed.groupby(['city','label']).size().to_dict().__str__(),
          'n_industrial_sites':int(y.sum()),'n_school_controls':int(df.site_type.astype(str).str.contains('school').sum()),'negative_categories':df.loc[df.label.eq(0),'site_type'].value_counts().to_dict(),'feature_count':len(cols),
          'candidate_components_cv_accuracy':scores,'selected_pca_components':best,
          'test_accuracy':float(accuracy_score(y[te],prediction)),'test_auc':float(roc_auc_score(y[te],prob)),
          'test_precision':float(precision_score(y[te],prediction)),'test_recall':float(recall_score(y[te],prediction)),
          'test_confusion_matrix_school_industrial':cm,
          'interpretation':'Registry and OSM polygon labels are proxies; small held-out site set; score is not factory-wide accuracy or emission attribution.'}
 (out/'all_city_test_metrics.json').write_text(json.dumps(summary,indent=2))
 joblib.dump({'model':m,'features':cols,'split':'city-balanced test sites','train_ids':df.iloc[tr].facility_id.tolist()},out/'all_city_test_model.joblib')
 # Deployment scores use all observed examples; never substitute them for test predictions.
 full=estimator(best).fit(X,y)
 joblib.dump({'model':full,'features':cols,'label_scope':'EPA TRI registry points versus OSM school, green and commercial polygon proxies' if expanded else 'EPA TRI registry points versus OSM schools'},out/'factory_screen_model.joblib')
 df['factory_screen_score']=full.predict_proba(X)[:,1]
 df[df.label.eq(1)][['facility_id','name','city','latitude','longitude','label','factory_screen_score']].to_csv(out/'factory_screening_results.csv',index=False)
 fig,ax=plt.subplots(figsize=(6,3));ax.bar(['Train CV','All-city test'],[scores[best],summary['test_accuracy']],color=['#548984','#173e3d']);ax.set_ylim(0,1);ax.set_ylabel('Accuracy');ax.set_title(f'Site-level spectral screen (n={len(tr)} train; n={len(te)} test)');fig.tight_layout();fig.savefig(out/'all_city_test_metrics.png',dpi=150);plt.close(fig)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--expanded',action='store_true');args=parser.parse_args();run(expanded=args.expanded)
