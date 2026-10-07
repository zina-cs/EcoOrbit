"""Plot only QA-valid, previously observed TROPOMI regional CH4 context."""
from pathlib import Path
import pandas as pd,matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/real/methane';ATM=ROOT/'results/real/atmosphere'
def run():
 rows=[]
 for city in ('Jacksonville','Detroit','Rochester'):
  p=ATM/f'{city.lower()}_ch4.csv'
  if p.exists():
   for _,r in pd.read_csv(p).iterrows():
    if pd.notna(r.get('median')) and r.get('n_valid',0)>0:
     rows.append({'city':city,'date':r['date'],'median_xch4_ppb':r['median'],'p95_xch4_ppb':r['p95'],'n_valid_pixels':r['n_valid'],'scene_id':r['scene_id']})
 out=pd.DataFrame(rows);OUT.mkdir(exist_ok=True);out.to_csv(OUT/'observed_us_regional_ch4.csv',index=False)
 if not out.empty:
  fig,ax=plt.subplots(figsize=(7,3.5));ax.scatter(out.city+'\n'+out.date,out.median_xch4_ppb,color='#277a78',s=85);ax.set(ylabel='Median XCH4 (ppb)',title='QA-valid regional TROPOMI CH4: observed US scenes');ax.set_ylim(1850,2000);fig.tight_layout();fig.savefig(OUT/'observed_us_regional_ch4.png',dpi=150);plt.close(fig)
 print(out.to_string(index=False))
if __name__=='__main__':run()
