# EcoOrbit ESG evidence readiness | observed US pilot

**Sites:** 24 EPA TRI-associated industrial points (eight each in Jacksonville, Rochester and Detroit). **Period:** source Tanager scenes dated 16 May, 1 August and 14 September 2025. **Target for future work:** Fujairah, UAE. This is a research screen, not a company emissions inventory, causal plume finding or UAE legal-compliance report.

## Evidence by topic

| Topic | Observed result in this package | What remains unresolved |
|---|---|---|
| Industrial-site hyperspectral screen | 24 registry points versus 24 mapped schools; leave-one-city-out pooled accuracy 0.750 and ROC AUC 0.804 | Narrow school-only negative class, point-versus-parcel uncertainty and operating status |
| Surface heat | Landsat L2, 38 site-date rows for 19 distinct industrial sites; 3 Detroit, 8 Jacksonville, 8 Rochester | Surface mix and different dates confound industrial process-heat inference |
| Land change | Two-date Sentinel-2 NDVI/NDBI at 8 paired sites: 2 Detroit and 6 Jacksonville | Rochester selected scenes had no valid site pixels; dates not phenology-matched |
| Satellite NO2 and SO2 | QA-valid regional TROPOMI columns at 8 Detroit points, with nearest pixel-center distance and scene ID | Rochester image-week catalog gap; Jacksonville download pending; no site attribution or ground concentration |
| Additional atmospheric context | CAMS modeled NO2 and SO2, 168 hourly entries per city; older Sentinel-2 AOT and Sentinel-5P methane/UV aerosol outputs are available | Model grid and multi-kilometre pixel footprints cannot quantify factory discharge |
| Wind | ERA5 10 m hourly wind for each city | Does not represent stack-height direction or a dispersion simulation |
| Scope 1 and Scope 2 | Not calculated | Metered fuel/electricity, organizational boundary, factors and audit trail needed |
| UAE permits and reporting | Not assessed | Verified Fujairah sites, applicable permits, current UAE/emirate rules and validated monitoring needed |

Median Landsat site-minus-nearby-land surface contrast across available site-date rows: Detroit +0.66 C, Jacksonville +1.45 C and Rochester +4.00 C. These **are not comparable factory emission rates**; the weather, acquisition dates, land cover and scene coverage differ. The NO2 and SO2 files store column mol/m2, not µg/m3 at ground level. Negative SO2 retrievals near background are retained as noisy retrievals, never treated as negative emissions.

## Missing-data register and recommended next evidence

| Missing item | Current treatment | What to collect next |
|---|---|---|
| Five Detroit site points lack valid Landsat results in the two selected scenes | No temperature assigned | More clear thermal scenes or verified facility polygons |
| Rochester paired Sentinel-2 change | No change computed | Clear scenes that cover the actual site footprint in comparable seasons |
| Rochester NO2/SO2 in 1-9 August 2025 | No catalog item, not zero | Query another date and label temporal separation |
| Jacksonville NO2/SO2 in this ZIP | Download pending, not zero | Run city/product-specific download command with adequate disk/network |
| Factory GHG and regulated pollutant quantities | Not estimated | Metered activity, stack/fenceline observations, dispersion model and uncertainty assessment |

The dashboard can be opened now with `streamlit run dashboard.py`. Exact source IDs, dates, QA thresholds, pixel distances and coverage are in `results/real/` tables. The method and satellite-source table are in `docs/methodology.md` and `README.md`.


Update: Jeddah 2024-06-09 now has actual EMIT pixel analysis; see `docs/EMIT_PIXEL_METHOD.md`. Integrated excess mass and diagnostic flux scenarios are available, but validated facility rates and annual Scope 1 totals remain unavailable.
