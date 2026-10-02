# Training register source snapshots

`frs_30.35.json`, `frs_43.15.json`, `frs_42.28.json` were retrieved 27 September 2026 from the U.S. EPA Facility Registry Service `get_facilities` API, with `latitude83`, `longitude83`, `search_radius` (12 or 15 miles), `pgm_sys_acrnm=TRIS`, and `output=JSON`. Source: https://www.epa.gov/frs/frs-api . The 24 industrial-site IDs are explicitly selected in `src/build_training_register.py`; their individual EPA source links are retained in `data/training_sites.csv`.

`osm_schools_*.json` were retrieved the same day using OpenStreetMap Nominatim bounded search `q=school`, `limit=50` in each Tanager scene's bounding box. Source: https://nominatim.openstreetmap.org/search . Retained school sites are at least 650 m from selected industrial points and each other and pass the Tanager clear-pixel check. OpenStreetMap data are © OpenStreetMap contributors under ODbL.

FRS TRI inclusion indicates a registry entry; it does not verify that each facility is currently operating or delineate its parcel. OSM schools are a narrow comparison class. This register supports an exploratory site screen, not a general factory classifier. The snapshots allow the selection to be repeated without hitting public API rate limits.
