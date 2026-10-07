"""Map observed NASA CMR EMIT plume-complex geometries by landfill."""
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
ROOT=Path(__file__).resolve().parents[1]
def run():
 d=pd.read_csv(ROOT/'results/real/landfill_gases/emit_search.csv')
 sites=pd.read_csv(ROOT/'data/landfill_sites.csv')
 fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
 colors=['#23ad8f','#e9a84c','#6c97d7']
 for ax,site in zip(axes,sites.itertuples()):
  q=d[(d.site_id==site.site_id)&(d.gas=='CH4')]
  for i,r in enumerate(q.itertuples()):
   outlines=json.loads(r.plume_outline_json)
   date=r.granule_id.split('_')[4][:8]
   label=f'{date[:4]}-{date[4:6]}-{date[6:]} ({r.plume_distance_km:g} km)'
   for j,poly in enumerate(outlines):
    ax.add_patch(Polygon(poly,closed=True,facecolor=colors[i%len(colors)],edgecolor=colors[i%len(colors)],alpha=.42,label=label if j==0 else None))
  ax.scatter(float(site.longitude),float(site.latitude),marker='x',s=100,color='#1b2733',linewidths=2,zorder=5,label='Approx. landfill point')
  ax.set_xlim(float(site.longitude)-.055,float(site.longitude)+.055)
  ax.set_ylim(float(site.latitude)-.065,float(site.latitude)+.065)
  ax.set_title(site.name)
  ax.set_xlabel('Longitude (°)');ax.set_ylabel('Latitude (°)');ax.grid(alpha=.18)
  ax.legend(loc='lower left',fontsize=7,framealpha=.9)
 fig.suptitle('NASA EMIT V002 CH₄ plume-complex catalog geometry, 2024',fontweight='bold')
 fig.text(.5,-.035,'NASA CMR geometry and published approximate site points; proximity does not prove landfill source.',ha='center',fontsize=9)
 out=ROOT/'results/real/landfill_gases/emit_landfill_footprints.png'
 out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=170,bbox_inches='tight');plt.close(fig)
 print(out)
 return out
if __name__=='__main__':run()
