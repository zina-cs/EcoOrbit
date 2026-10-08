# EcoOrbit — methane and carbon intelligence

**Team:** EcoOrbit · **Challenge:** Air Intelligence

This PoC focuses on real hyperspectral methane plume analysis and traceable carbon evidence. NO₂/SO₂, site classification, Sentinel-2 multispectral change and Landsat heat provide supplementary investigation context.

## Judge walkthrough

1. **Solution:** select Jeddah or a Seropédica event, inspect real pixels and wind, compare threshold-dependent mass and diagnostic flux, then review separate published CH₄/CO₂ references.
2. **Methodology:** follow acquisition, provider calibration/correction, EcoOrbit QA/geometry/binning, gas analysis, supplementary ML and reporting. Each step names the implemented code.
3. **Additional features:** inspect completed US maps, hyperspectral materials/site classification, multispectral indices, heat and relevant NO₂/SO₂. These examples have their own locations and dates.

**Evidence boundary:** NASA supplies spectral gas retrievals. EcoOrbit analyzes delivered gas pixels; its ML is a small industrial-versus-school contextual screen. CO₂ is source-reported reference evidence, not a new landfill CO₂ retrieval. Computed gas flux scenarios are unvalidated and excluded from annual inventories.

```bash
python -m pip install -r requirements.txt
python -m src.emit_cases
python -m src.evaluate_sites
python -m src.build_website
```

Open `EcoOrbit_Results_Website.html`. Use `notebooks/02_main_analysis.ipynb` and `notebooks/04_emit_pixel_analysis.ipynb`. See `docs/methodology_report.pdf` and `docs/EMIT_PIXEL_METHOD.md` for the actual pipeline and assumptions.

---


The primary reproducible gas workflow processes three real NASA EMIT observations: **Jeddah, Saudi Arabia (9 June 2024)** and **Seropédica, Brazil (5 March and 24 September 2024)**. Source plume TIFFs, associated metadata, Jeddah enhancement/uncertainty/sensitivity crops, real ERA5 wind responses and processed outputs are bundled. No Earthdata account or new download is required for these three cases. Additional catalog dates and optional OCO observations are separate discovery workflows. Supplementary US examples cover 24 industrial and 24 school comparison sites across Detroit, Jacksonville and Rochester, plus green-patch context. These are separate locations, not landfill gas measurements.

| Bundled methane case | Product | Analysis |
|---|---|---|
| Jeddah · 2024-06-09 | EMIT CH4PLM + ENH/UNCERT/SENS crops | Sensitivity correction, background subtraction, uncertainty screening, excess mass and diagnostic wind flux |
| Seropédica · 2024-03-05 | EMIT CH4PLM + metadata | Vetted plume pixels, threshold selection, excess mass and diagnostic wind flux |
| Seropédica · 2024-09-24 | EMIT CH4PLM + metadata | Vetted plume pixels, threshold selection, excess mass and diagnostic wind flux |

Brazil has no bundled ENH/UNCERT/SENS companions; the code does not invent those corrections or sensor uncertainty. Calculated whole-complex flux is a diagnostic scenario, not a validated landfill emission rate. CO2 is a separate published reference; no landfill CO2 pixel retrieval or annual carbon inventory is claimed.

## Submission snapshot and business use case

**Project:** EcoOrbit — Earth-observation environmental screening for industrial sites. **Team:** EcoOrbit; enter member roles before submission. **Challenge:** Air Intelligence; confirm the exact registered theme on the platform. **Country:** enter the team's registered country. The intended end user is an environmental analyst or ESG reporting team deciding which facilities warrant a closer inspection and what evidence remains missing for disclosure. Industrial emissions are hard to screen consistently over a broad area; Earth observation supplies repeated regional context and hyperspectral land-use features. This is a research PoC and does not declare legal compliance or source attribution.

### Reproduce the headline result in a clean clone

Requires **Python 3.11**. The root has a pinned `requirements.txt`, a runnable notebook with committed outputs, real processed Tanager features in `data/sample_input/tanager_site_features_real.csv`, and example figures in `results/real/`. From the project root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
jupyter nbconvert --to notebook --execute notebooks/02_main_analysis.ipynb --output /tmp/ecoorbit-executed.ipynb
python -m src.import_methane_plumes --published
python -m src.emit_cases
python -m src.build_website
```

Open `EcoOrbit_Results_Website.html` directly in a browser. The notebook normally takes a few minutes on a laptop, needs no GPU, and reproduces the **11/12 held-out industrial-versus-school classifier result** from observed site spectra. It also reads QA-screened heat and atmospheric summaries, validates three source-linked real plume examples, and rebuilds the website. Raw Tanager scenes and optional Sentinel refreshes require several GB and are documented later; the reviewer path needs no tokens. Run `streamlit run dashboard.py` for the separate local Streamlit app. See `docs/GITHUB_SETUP.md` for macOS/Windows GitHub publishing and validation.

![Held-out classifier result](results/real/classifier/all_city_test_metrics.png)

![Observed land surface heat](results/real/heat/site_heat.png)

### Data, processing, and disclosure

The data table below gives products, providers, windows and outputs. Tanager is provider-calibrated, atmospherically corrected and orthorectified **L2A**, then binned into 57 reflectance features; the pipeline masks invalid pixels and adds three indices. A site-level train/test split across all cities, train-only PCA selection and logistic regression produce the reported metric. Landsat L2 surface temperatures use scale/offset and QA masking; Sentinel-2 L2A uses scene classification masking and NDVI/NDBI; Sentinel-5P L2 uses product QA screens. The atmosphere, heat and plume results retain their units and coverage gaps. Validation includes the fixed 36/12 site split; generalization to new cities or land-use classes is unproven.

Third-party terms and attribution are in `docs/DATA_ATTRIBUTION.md`; the MIT LICENSE covers EcoOrbit's code only. The team roles, official theme and slide title must be filled with your actual registration. No secrets or raw restricted scenes should be committed. The supplied slide deck is `docs/slides.pdf`; attach the PDF to the platform form. The source guide requires a GitHub repository **and** the form submission.

## Methane-first workflow

The case register is `data/methane_sites.csv`; dated search windows are `data/methane_windows.csv`, including CTR Santa Rosa for the independent landfill comparison. The Stanford controlled-release experiment at 32.82182, -111.78577 is documented in **October–November 2022**. The suggested August 2024–December 2025 period is not verified in the cited study. Hassi R'Mel is represented by an approximate gas-field coordinate, not a surveyed compressor stack. Wadi Al-Asla landfill is at about 21.6442, 39.3903; the three proposed 2024 dates now coincide with NASA EMIT V002 CH4 plume-complex granules near the approximate site coordinate; source attribution requires source-geometry and wind validation; the June observation is processed in the bundled pixel workflow.

```bash
python -m src.methane_cases --site jeddah_landfill --max-scenes 8
python -m src.methane_cases --site hassi_rmel --max-scenes 8
python -m src.methane_cases --site stanford_arizona --max-scenes 8
# Optional: export a CH4 plume list from data.carbonmapper.org as CSV or GeoJSON
python -m src.import_methane_plumes /path/to/carbon_mapper_plumes.csv
```

The TROPOMI output (`results/real/methane/regional_ch4.csv`) compares QA-valid XCH4 (ppb) within 25 km with a 25–80 km ring, requiring at least three pixels in each. This is regional context and cannot identify a particular stack or landfill. The optional Carbon Mapper import preserves plume time, quality, sensor, instantaneous emission estimate, uncertainty and wind, matching reported plume origins within 20 km of each registered site; proximity alone does not establish source attribution. Download an [export from Carbon Mapper](https://data.carbonmapper.org/) and inspect the original plume image and source geometry. NASA [EMIT V2](https://search.earthdata.nasa.gov/) plume products are an additional hyperspectral option; V1 CH4 distribution ended in March 2026. No synthetic plume or CH4 measurement is included.

## Independent NASA landfill CH4 and CO2 workflow

**Observed NASA EMIT V002 CH4 catalog results, 2024-2025 query** (`results/real/landfill_gases/emit_search.csv`):

| Landfill | Date (UTC) | NASA EMIT CH4 plume-complex ID | Nearest CMR geometry to approximate point |
|---|---|---|---:|
| Wadi Al-Asla, Jeddah | 2024-02-26 | `EMIT_L2B_CH4PLM_002_20240226T074353_002767` | 0.611 km |
| Wadi Al-Asla, Jeddah | 2024-06-09 | `EMIT_L2B_CH4PLM_002_20240609T050226_003220` | 0 km (point within CMR polygon) |
| Wadi Al-Asla, Jeddah | 2024-10-15 | `EMIT_L2B_CH4PLM_002_20241015T114923_003697` | 1.115 km |
| CTR Santa Rosa, Seropédica | 2024-03-05 | `EMIT_L2B_CH4PLM_002_20240305T123325_002889` | 0 km |
| CTR Santa Rosa, Seropédica | 2024-09-24 | `EMIT_L2B_CH4PLM_002_20240924T133617_003564` | 0.277 km |

EMIT L2B plume complexes are manually reviewed by NASA's product team; the CMR polygon and approximate site point are real geospatial metadata. A close footprint **does not establish that the landfill emitted the gas**. Inspect the original GeoJSON outline, enhancement raster, wind, neighboring sources and facility boundary before attribution. No EMIT CO2 plume granule intersected the two search areas in the 2024-2025 query; that does not imply zero CO2 emissions. The NASA CMR footprint visualization is shown below. EMIT enhancement is ppm m, not kg/h or annual CO2e. The previous Carbon Mapper Brazil article remains a separate source-linked observation; it is not used for this NASA result.

![NASA EMIT V002 CH4 catalog footprints near Jeddah and Seropedica](results/real/landfill_gases/emit_landfill_footprints.png)

```bash
python -m pip install -r requirements-remote.txt
python -m src.landfill_gases --search-emit --start 2024-01-01 --end 2025-12-31
# Optional full products: prompts for NASA Earthdata login; caches downloads outside git
python -m src.landfill_gases --search-emit --site jeddah_landfill --start 2024-02-24 --end 2024-10-17 --download
python -m src.landfill_gases --emit-dir data/cache/emit_landfills
# Optional regional carbon dioxide: download NASA OCO-2/3 L2 Lite NetCDF at GES DISC
python -m src.landfill_gases --search-oco --site jeddah_landfill --start 2024-02-24 --end 2024-02-28
# Add --download to authenticate and process the matching NASA Lite daily files
python -m src.landfill_gases --oco /path/to/oco2_or_oco3_lite.nc4
# Optional regional methane for the two landfill sites, large S5P orbital downloads
python -m src.methane_cases --site jeddah_landfill --max-scenes 8
python -m src.methane_cases --site seropedica_landfill --max-scenes 8
python -m src.build_website
```

An OCO daily granule overlapping a search box is only a discovery result; it may have zero usable local soundings. The OCO module requires QA-good `xco2_quality_flag == 0`, at least three soundings within 25 km and three in a 25-80 km reference ring before reporting an XCO2 contrast in ppm. This is **regional context only**, not landfill CO2 emission. If the Lite file has no local pass, status remains insufficient coverage. NASA Earthdata login is needed for protected downloads; never commit credentials or raw scenes. The website's **Landfill gases** tab maps the five observed NASA catalog footprints, dates and distances and separately shows OCO/Sentinel coverage.

## Satellite and other data actually used

| Source | Date or window | Purpose | Included result |
|---|---|---|---|
| Sentinel-5P TROPOMI L2 CH4 | US 2025 observations supplied; target windows pending download | Regional XCH4 QA and background comparison | `results/real/atmosphere/`, `methane/` |
| Carbon Mapper / EMIT or Tanager methane plume export | Optional, none included for three target cases | Plume origin, instantaneous rate, uncertainty and wind, after source validation | `src/import_methane_plumes.py` |
| Planet Tanager orthorectified L2A, 426-band HDF5 | Jacksonville 2025-05-16; Rochester 2025-08-01; Detroit 2025-09-14 | Provider-corrected hyperspectral source for 24-site classifier | `results/real/classifier/` |
| Landsat 8/9 Collection 2 L2 thermal | Selected clear scenes around each Tanager date | Site versus surrounding land surface temperature | `results/real/heat/` |
| Sentinel-2 MSI L2A red, NIR, SWIR and SCL | Two seasonal windows per city | Site NDVI/NDBI vegetation and built-surface change | `results/real/land/` |
| Sentinel-5P TROPOMI L2 NO2/SO2 NetCDF | Image-week scenes where available | Nearby QA-valid atmospheric column pixel and center distance | `results/real/pollutants/` |
| Sentinel-2 AOT and Sentinel-5P CH4/UV aerosol index | Selected 2025 scene-week observations | Optional older aerosol/methane regional context | `results/real/aot/` and `results/real/atmosphere/` |
| CAMS global model; ERA5 reanalysis | 168 hourly entries per city | Regional modeled air and 10 m wind | `results/real/air_by_city.csv`, `wind_by_city.csv` |
| EPA FRS TRI and OSM school points | Source snapshots queried 2026-09-27 | Weak industrial/school training labels and coordinates | `data/training_sites.csv`, `data/source_snapshots/` |

CAMS and ERA5 are **not satellites**. No Arab Satellite 813, EnMAP, PlanetScope or Fujairah image is used here. Tanager item IDs are `20250516_164837_16_4001`, `20250801_165548_86_4001` and `20250914_171527_18_4001`. The source HDF5 files total roughly 3.3 GB and are downloaded on demand. The ZIP contains processed observed outputs, source-record snapshots and the trained model, but excludes raw caches.

## Run on your machine

Install Python 3.11 or 3.12 and unzip this archive. From inside the extracted `EcoOrbit_v2` folder:

```bash
python -m venv .venv
source .venv/bin/activate              # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run dashboard.py
```

The dashboard works immediately from included outputs. **A Gemini API key is not required to open the app or inspect any results tab.** The EcoOrbit Chat tab stays available but only replies after a key is provided. Open the Methane cases tab first; target locations have explicit pending statuses while measured US regional CH4 context is shown. Select a city and factory to inspect the map, held-out classifier scores, heat and land-change tables, QA-filtered pollutant columns and wind/ESG evidence. The methodology diagram and detailed report are in `docs/methodology.md` and `docs/methodology_report.pdf`. A short submission deck is `docs/slides.pdf`.

## EcoOrbit Chat (optional Gemini key)

The **EcoOrbit Chat** tab is an on-topic explainable-AI helper for this PoC. It answers from bundled results, methodology and README material (methane pixels, classifier metrics, coverage limits, ESG gaps). It declines unrelated questions. The chat uses Google Gemini; without a key the tab explains how to add one and the rest of Streamlit still runs.

Do **not** put an API key in `requirements.txt` (that file is only Python packages) and do not commit a key.

**Easiest for judges:** open the dashboard, go to EcoOrbit Chat, paste a free key from [Google AI Studio](https://aistudio.google.com/apikey) into the key box, then ask a starter question. The key stays in the browser session and is not written to disk.

Optional, if you prefer not to paste each time (PowerShell):

```bash
$env:GEMINI_API_KEY="your_key_here"
streamlit run dashboard.py
```

A local `.env` file with `GEMINI_API_KEY=your_key_here` is also read if present. Never commit `.env`.

To reproduce from public sources, run the notebook **from the project root** (`jupyter lab notebooks/02_main_analysis.ipynb`) or execute:

```bash
python -m src.multisite_download
python -m src.build_training_register
python -m src.expand_candidates
python -m src.train_classifier  # requires the three raw Tanager HDF5 scenes
python -m src.evaluate_sites  # reproducible all-city test from included real spectra
python -m src.green_reference  # observed Jacksonville vegetation comparison
python -m src.gri_report
python -m src.regional
python -m src.multisite_aerosol
python -m src.site_heat
python -m src.site_land
python -m src.site_pollutants
```

Allow at least **8 GB free disk** and a stable Internet connection; the full Sentinel-5P orbital NetCDF files can be large. Downloads cache resumable 8 MiB parts. To finish only the pending Jacksonville pollutant outputs without redoing Detroit:

```bash
python -m src.site_pollutants --city Jacksonville --product no2
python -m src.site_pollutants --city Jacksonville --product so2
```

The command retains other cities' completed rows. `src.atmosphere` separately refreshes the legacy CH4 and UV aerosol context if desired. No additional file or Google factory lookup is required for the included US pilot. For new regions, supply verified factory and comparison coordinates, actual hyperspectral scene coverage and preferably surveyed parcel polygons; the current 48 labels must not simply be reused for Fujairah.

## Observed coverage and meaning

| Output | Detroit | Jacksonville | Rochester | Overall |
|---|---:|---:|---:|---:|
| Registry industrial points passing Tanager source-pixel QA | 8 | 8 | 8 | 24 |
| Landsat distinct sites with valid temperature | 3 | 8 | 8 | 19 (38 site-date rows) |
| Paired Sentinel-2 NDVI/NDBI change | 2 | 6 | 0 | 8 |
| QA-valid Sentinel-5P NO2 **and** SO2 in the supplied ZIP | 8 | Download pending | No catalog item in queried image week | 8 per product |

The 60-feature Tanager site model uses 57 reflectance bins and three spectral indices, PCA and logistic regression. For the requested site-level test across all three cities, the fixed 36/12 city-and-label-stratified split gives **11/12 = 0.917 accuracy** and **0.944 ROC AUC**, with two industrial and two school test sites per city. PCA choice uses training-only three-fold cross-validation. The previous city-holdout result (0.750 accuracy and 0.804 AUC) remains a harder geographic-transfer check and is not directly comparable. This is an EPA-listed industrial-neighborhood versus mapped-school screen, not a validated classifier of every factory or nonfactory land use.

Landsat measures **land surface temperature**, not stack heat. Sentinel-2 index changes have seasonal and land-cover confounding. Sentinel-5P NO2/SO2 pixels span kilometres and can contain several factories: the table reports the nearest QA-valid **pixel center**, its distance and atmospheric column in mol/m², not a factory emission or ground concentration. Missing and pending values are never interpreted as zero. CAMS air and ERA5 wind are regional context. Scope 1/2 and UAE permit compliance are **not assessed** without audited activity, factors, monitoring, permits and verified site boundaries.

`data/sample_input/tanager_site_features_real.csv` contains real extracted Tanager features. Unused synthetic fixtures have been removed. The source files are documented in `docs/methodology.md`; the dashboard report is `results/real/esg_evidence_report.md`.

## Expansion and international reporting

`data/candidate_factories.csv` contains 424 additional EPA FRS records inside the three scene bounding boxes. These **are not measured, QA-approved factory training sites**; registry coordinates may be offset, historical, or nonindustrial. To increase the trained sample, download the three provider Tanager L2A HDF5 files using the scene IDs listed in `data/training_sites.csv`, place them as `data/cache/<scene_id>_ortho_sr.h5`, verify each new site's operation and geometry, check the clear pixel and valid 11×11 neighborhood, and extract features with `src.train_classifier.site_features`. Obtain varied nonindustrial control polygons (residential, retail, offices, parks and transportation) from OSM or authoritative local land-use data, verify them against imagery, then rebuild the split by site and rerun evaluation. Never append candidate rows directly to `site_spectral_features.csv`.

Schools originally provided geocoded built-up negatives for the 48-site demonstration. They help test whether the spectral signature differs from those locations, but cannot establish classification accuracy against all nonindustrial land uses. The GRI 305 / GHG Protocol evidence-gap output is `results/real/esg_gri305_evidence.md`; satellite columns cannot supply facility Scope 1/2 or NOx/SOx mass quantities. See [GRI 305](https://www.globalreporting.org/publications/documents/english/gri-305-emissions-2016/) and the [GHG Protocol Corporate Standard](https://ghgprotocol.org/corporate-standard).

## Add green space and commercial comparisons

The current 48-site measured result still compares industrial registry points with schools. To obtain **real, additional negative classes** from OSM parks/grass/forest and commercial/retail/office polygons inside the same Tanager scenes, run the following after installation. The OSM API and source HDF5 files must be reachable from your machine.

```bash
python -m src.add_control_sites --fetch
python -m src.multisite_download
python -m src.add_control_sites --extract
python -m src.evaluate_sites --expanded
```

`--fetch` saves raw OSM responses to `data/source_snapshots/osm_landuse_<city>.json` and a `data/candidate_controls.csv` register. `--extract` selects up to four clear, separated green sites and four commercial sites per city, with actual source-pixel spectra, retaining the existing school controls. It writes `results/real/classifier/site_spectral_features_expanded.csv`. `--expanded` writes a **new** trained model, site split, test predictions and metrics under `results/real/classifier/expanded/`; the test is stratified by city and site type. These proxy labels still require visual verification against imagery and operating records. If the polygons or clear pixels do not support a category, the script reports the actual number; it never creates substitutes. Green space provides a distinct vegetation-rich comparison; commercial properties provide built-up nonindustrial comparison. Neither is an attribution control for emissions or a guarantee of general land-use accuracy.

The package does not claim results from the new classes: the OSM service and three 3.3 GB HDF5 scenes could not be fetched from this execution environment. The included existing test metric remains the 48-site industrial-versus-school evaluation until the new data pass QA and the expanded evaluation is run.

## Included observed green-area comparison

The included `results/real/classified_sample.npz` is a QA-filtered, 60 m sampled grid of Jacksonville's **real Tanager L2A** spectral material classes. `src/green_reference.py` selects 12 spatially separated 5×5 sampled-cell patches with at least 80% pixels in its most vegetation-rich class and at least 95% valid pixels. Outputs are `results/real/green_reference_patches.csv`, `green_reference_summary.json`, `green_reference_map.png` and `green_reference_comparison.png`, all visible in the dashboard. The scene-wide green-cluster median NDVI is **0.770**, while the median of eight measured Jacksonville industrial-site 150 m neighborhoods is **0.305** (difference **+0.465**). The green cluster's median is a *single pixel-population summary*, not 12 separately measured park values. These are scene-pixel reference patches with image row/column addresses, not geocoded or OSM-verified parks. The comparison illustrates spectral vegetation contrast and does not estimate factory impact or change classifier test accuracy. The OSM polygon workflow above remains available for verified named green sites once source imagery can be downloaded.

## CO₂ plumes and carbon accounting

The **CH₄ and CO₂** dashboard tab interactively filters case location, dates and gas-specific Carbon Mapper plume records (when imported). The **NO₂, SO₂ and aerosols** tab selects a pollutant and city and shows observed column or regional-model values. Streamlit maps and charts respond to those selections; missing observations stay visibly missing. The existing US NO₂/SO₂ and two QA-valid regional CH₄ observations are included. There is **no EMIT CO₂ plume catalog match for the two landfills in the searched 2024-2025 period**, and no quality-screened OCO XCO₂ file bundled. This does not imply zero emission.

Carbon Mapper and NASA EMIT V2 provide hyperspectral CO₂ as well as CH₄ plume products. Export a Carbon Mapper CH₄/CO₂ plume list as **CSV or GeoJSON** and run:

```bash
python -m src.import_methane_plumes /path/to/plumes.csv
streamlit run dashboard.py
```

The resulting `results/real/methane/plume_matches.csv` records gas, plume ID, time, quality, wind, uncertainty and instantaneous **kg of that gas per hour**. A match within 20 km is a review candidate, never an attributed emission solely from proximity. Check the original plume image and reporting source. Do not sum or annualize spot rates.

To calculate reporting-period Scope 1 and Scope 2 **tonnes CO₂e**, copy `data/facility_activity_template.csv` to `data/facility_activity.csv` and enter your actual fuel/process activity, purchased electricity, matching kgCO₂e factors, source citations and period. Then run:

```bash
python -m src.carbon_results
python -m src.gri_report
streamlit run dashboard.py
```

The result appears in the **Carbon and ESG results** tab. Without the ledger, it shows an explicit unavailable status, not zero. The supplied factor must already embody the gases and GWP basis appropriate to its source. For direct CO₂ only, enter a CO₂-specific factor and describe its basis; for a full Scope 1 CO₂e inventory, account for all material gases and processes. The current one-row-per-facility-period template supports one aggregated fuel/process factor and one electricity factor; extend it for multiple fuels and separate Scope 2 location/market methods rather than combine incompatible factors. Consult [GHG Protocol Corporate Standard](https://ghgprotocol.org/corporate-standard), [Scope 2 Guidance](https://ghgprotocol.org/scope-2-guidance) and [GRI 305](https://www.globalreporting.org/publications/documents/english/gri-305-emissions-2016/).

## Published real plumes included

The first dashboard tab now contains **source-linked, real hyperspectral plume observations**, with gas-specific filters and source image links:

| Site | Gas | Acquisition | Reported rate | Evidence |
|---|---|---|---:|---|
| Seropédica landfill, Brazil | CH4 | 29 Sep 2024, Tanager-1 | preliminary 2,836 kg CH4/h | Carbon Mapper article and named plume image |
| Singrauli electricity generation, India | CO2 | 1 Nov 2024, Tanager-1 | preliminary source rate 838,000 kg CO2/h | Carbon Mapper article and named plume image |
| Carbon Mapper published API example | CH4 | 20 Apr 2024, EMIT | 3,610.58 ± 377.95 kg CH4/h | Carbon Mapper product guide: ID, coordinates, quality and wind |


## Google Colab

Open `Run_EcoOrbit_Colab.ipynb` in [Google Colab](https://colab.research.google.com/) and upload the project ZIP through the **Files sidebar**. Run extraction and installation, then **Build and download the results website**. Colab downloads `EcoOrbit_Results_Website.html`; open that file in your browser. It is a self-contained interactive website with maps, filters, charts, source notes and methods. No localhost proxy is required. To regenerate after new outputs, run `python -m src.build_website` from the project root. The optional notebook-native controls and direct `show_section('Heat')` remain for quick inspection. For local Streamlit, run `streamlit run dashboard.py`.

## Run the earlier factory, heat and NO₂/SO₂ analyses in Colab

The revised `Run_EcoOrbit_Colab.ipynb` includes a **Previous analysis** section after dashboard startup. Run its classifier cell to retrain from the 48 bundled real Tanager site spectra, then run the heat and gas cells to inspect the existing QA-screened outputs. These cells work without new satellite downloads. The dashboard tabs **Hyperspectral classification**, **Surface context**, and **NO₂, SO₂ and aerosols** show the same results interactively.

To refresh from remote scenes, uncomment one command at a time in the notebook's final **Optional: refresh satellite scenes** cell. NO₂ and SO₂ accept a city and product to limit the download. `src.site_heat` searches Landsat scenes for all three cities. `src.multisite_download` obtains the much larger original Tanager HDF5 scenes; only then can `src.train_classifier` re-extract raw site spectra. Keep existing result files backed up if you intend to compare before and after reprocessing.

## Real Jeddah pixel analysis (9 June 2024)

Uploaded NASA EMIT V002 ENH/UNCERT/SENS rasters now support actual pixel analysis. Small spatial crops retaining original pixel values are included in `data/real_emit/jeddah_20240609/`, with original plume TIFF/GeoJSON and real ERA5 archive response. No login or download is required for this case.

```bash
python -m src.emit_pixels
python -m src.build_website
```

Open the Landfill gases tab or `notebooks/04_emit_pixel_analysis.ipynb`. The website includes hoverable pixel measurements, mask threshold controls, integrated excess methane mass and an explicitly unvalidated Simple-IME flux scenario. Facility emission rate remains unavailable because source origin, steady single-source geometry and appropriate wind are not established. See `docs/EMIT_PIXEL_METHOD.md`. These scenario values are excluded from ESG inventories. Existing methodology PDFs predate this new module; use this addendum for its methods and findings.

## Three real landfill plume observations

Run `python -m src.emit_cases` then `python -m src.build_website` for Jeddah (9 June 2024) and Seropédica (5 March / 24 September 2024). Original Brazil plume rasters/GeoJSON and real cached ERA5 responses are bundled alongside Jeddah source-scene crops. No credentials or further download is required for these inputs. The Landfill methane tab has an event selector, hoverable pixels and threshold sensitivity. Brazil PLM-only analysis and Jeddah corrected analysis are distinguished. All computed fluxes are diagnostic scenarios excluded from ESG totals. Read `docs/EMIT_PIXEL_METHOD.md`; run `notebooks/04_emit_pixel_analysis.ipynb`. Optional unexecuted website panels have been removed.
