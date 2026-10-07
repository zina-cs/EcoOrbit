"""Observed Jacksonville Tanager vegetation-patch comparison.

Uses the archived QA-filtered classified pixel grid and observed site features.
Patch centers are image row/column indices (60 m sampled grid), not surveyed
park coordinates. Cluster-wide index medians are not per-patch measurements.
"""
from pathlib import Path
import json
import numpy as np,pandas as pd,matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/real'
def run():
 with np.load(OUT/'classified_sample.npz') as z:
  labels=z['cluster'];valid=z['valid']
 clusters=pd.read_csv(OUT/'spectral_clusters.csv')
 factories=pd.read_csv(OUT/'classifier/site_spectral_features.csv')
 factory=factories[(factories.city=='Jacksonville') & (factories.label==1)]
 # Strongest measured vegetation-like class, selected by cluster NDVI.
 green=clusters[clusters.name.eq('vegetation-like')].sort_values('ndvi',ascending=False).iloc[0]
 target=int(green.cluster);patches=[]
 for row in range(3,labels.shape[0]-3,4):
  for col in range(3,labels.shape[1]-3,4):
   patch=labels[row-2:row+3,col-2:col+3]
   fraction=float((patch==target).mean());clear=float((patch>=0).mean())
   if fraction>=.8 and clear>=.95:patches.append((row,col,fraction,clear))
 chosen=[]
 for row,col,fraction,clear in patches:
  if all((row-p['image_row'])**2+(col-p['image_col'])**2>=30**2 for p in chosen):
   chosen.append({'reference_id':f'JAX_GREEN_{len(chosen)+1:02d}','city':'Jacksonville','image_date':'2025-05-16',
    'image_row':row,'image_col':col,'patch_width_m_approx':300,'dominant_cluster':target,
    'dominant_fraction':fraction,'valid_fraction':clear,
    'site_type':'Tanager vegetation-rich image patch; parcel status unverified'})
  if len(chosen)==12:break
 if len(chosen)<8:raise ValueError('Insufficient spatially separated clear green patches')
 pd.DataFrame(chosen).to_csv(OUT/'green_reference_patches.csv',index=False)
 summary={'scene_id':'20250516_164837_16_4001','green_patch_count':len(chosen),'factory_site_count':len(factory),
  'sampled_pixel_m':60,'patch_width_m_approx':300,'green_cluster':target,
  'green_cluster_pixels':int(green.pixels),'green_cluster_ndvi_median':float(green.ndvi),
  'green_cluster_ndbi_median':float(green.ndbi),'factory_site_ndvi_median':float(factory.ndvi.median()),
  'factory_site_ndbi_median':float(factory.ndbi.median()),
  'ndvi_reference_minus_factory':float(green.ndvi-factory.ndvi.median()),
  'comparison_scope':'Green cluster-wide median versus 8 factory-neighborhood medians; green patches are spatial reference locations, not 12 independent NDVI measurements or verified parks.',
  'limitations':'Unsupervised vegetation-like pixels; no OSM park polygon validation; different spatial supports; not classifier test data or evidence of factory emissions.'}
 (OUT/'green_reference_summary.json').write_text(json.dumps(summary,indent=2))
 fig,ax=plt.subplots(figsize=(8,7));ax.imshow(np.ma.masked_where(~valid,labels),cmap='tab10',vmin=0,vmax=9,interpolation='nearest')
 ax.scatter([x['image_col'] for x in chosen],[x['image_row'] for x in chosen],facecolors='none',edgecolors='white',s=95,lw=1.5,label='12 clear vegetation patches')
 ax.set(title='Jacksonville Tanager L2A | vegetation reference patches',xlabel='Sampled image column (60 m)',ylabel='Sampled image row (60 m)');ax.legend(loc='lower left');fig.tight_layout();fig.savefig(OUT/'green_reference_map.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(figsize=(6,4));ax.bar(['Factory-site median\n(n=8)','Vegetation cluster\n(14,052 pixels)'],[summary['factory_site_ndvi_median'],summary['green_cluster_ndvi_median']],color=['#555e67','#267e4f']);ax.set(ylabel='NDVI',ylim=(0,1),title='Observed hyperspectral vegetation contrast');fig.tight_layout();fig.savefig(OUT/'green_reference_comparison.png',dpi=150);plt.close(fig)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
