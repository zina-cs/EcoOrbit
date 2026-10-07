# Source data and redistribution

The MIT LICENSE applies to EcoOrbit code only. Third-party satellite, registry, model and plume data retain their providers' terms; this repository does not relicense them.

| Product | Provider / source | Included material | Access and terms to check |
|---|---|---|---|
| Tanager L2A hyperspectral | Planet Tanager scene items listed in README | Small derived site-feature table and classification figures; no raw scene | [Planet Tanager access](https://developers.planet.com/docs/data/tanager/) and scene license |
| Landsat 8/9 Collection 2 L2 | USGS/NASA | Derived site temperature summaries | [USGS Landsat](https://www.usgs.gov/landsat-missions/landsat-data-access) |
| Sentinel-2 and Sentinel-5P | Copernicus | Derived indices, AOT and QA-screened columns | [Copernicus Data Space](https://dataspace.copernicus.eu/) |
| CAMS and ERA5 | ECMWF/Copernicus | Regional hourly modeled air and reanalysis wind summaries | [CAMS](https://atmosphere.copernicus.eu/) and [ERA5](https://cds.climate.copernicus.eu/) attribution |
| EPA FRS TRI | US EPA | Point register and labels | [EPA FRS](https://www.epa.gov/frs) |
| OSM | OpenStreetMap contributors | School comparison points | [ODbL attribution](https://www.openstreetmap.org/copyright) |
| NASA EMIT V002 CH4/CO2 plume complexes | NASA LP DAAC / JPL | Five CMR metadata footprints and a derived map; no protected COGs | [EMIT L2B guide](https://github.com/emit-sds/emit-sds-tgp/blob/develop/docs/EMIT_L2B_TRACE_GAS_User_Guide.md); Earthdata login for download |
| OCO-2/3 Lite XCO2 | NASA GES DISC | No measurements bundled; optional parser | [OCO-3 Data Center](https://ocov3.jpl.nasa.gov/science/oco-3-data-center/) |
| Published CH4/CO2 plume examples | Carbon Mapper / EMIT / Tanager | Three attributed metadata rows with links, no embedded plume imagery | [Carbon Mapper terms](https://carbonmapper.org/terms): noncommercial purpose, attribution, share-alike on redistributed data |

Credit Carbon Mapper beside any plume graphic or copied record. Source metadata in `data/published_plumes.csv` includes the article and plume-image links. The website requests those plume images from the provider only when online; no third-party image bytes are committed. Recheck terms before sharing a larger portal export or licensed imagery publicly.
