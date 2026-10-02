"""Download the three exact public Planet Tanager L2A scenes for model training."""
from pathlib import Path
import json,requests,pandas as pd
COLLECTION='https://www.planet.com/data/stac/tanager-core-imagery/urban'

def download_all(registry='data/training_sites.csv',cache='data/cache'):
 cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
 for scene in sorted(pd.read_csv(registry).scene_id.unique()):
  item_path=cache/f'{scene}.json'
  if not item_path.exists():
   r=requests.get(f'{COLLECTION}/{scene}/{scene}.json',timeout=60);r.raise_for_status();item_path.write_bytes(r.content)
  item=json.loads(item_path.read_text());assert item['id']==scene
  url=item['assets']['ortho_sr_hdf5']['href'];path=cache/f'{scene}_ortho_sr.h5'
  if not path.exists():
   temp=path.with_suffix('.part')
   print('Downloading',scene,flush=True)
   with requests.get(url,stream=True,timeout=120) as response:
    response.raise_for_status()
    with temp.open('wb') as f:
     for chunk in response.iter_content(2**20):
      if chunk:f.write(chunk)
   temp.replace(path)
  print(scene,path.stat().st_size,'bytes',flush=True)
if __name__=='__main__':download_all()
