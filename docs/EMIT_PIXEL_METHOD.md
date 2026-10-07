# Jeddah methane pixel analysis — 9 June 2024

This addendum describes the new `src.emit_pixels` module and supersedes metadata-only descriptions for this event. Source: user-supplied NASA EMIT V002 files, observation 05:02:26 UTC, source scene `EMIT_L2B_CH4ENH_002_20240609T050226_2416104_002`. This is postprocessing of NASA's matched-filter retrieval, not an independent retrieval from L1B radiance.

## Reproduction

Install root requirements, then run `python -m src.emit_pixels` and `python -m src.build_website`. The real cropped input rasters are bundled in `data/real_emit/jeddah_20240609/`. Original pixel values and georeferencing are retained. The full uploaded source scene covers 2636 × 2707 pixels; only an analysis neighborhood is packaged. Output is `results/real/emit_pixels/jeddah_20240609/`. Notebook: `notebooks/04_emit_pixel_analysis.ipynb`.

## Steps and assumptions

1. Verify identical companion grids; honor no-data. Retain positive uncertainty and sensitivity in the analyst-chosen range 0.5–2. NASA says sensitivity division can amplify dim-pixel noise.
2. Calculate corrected enhancement as ENH/SENS. NASA's ATBD pixel-uncertainty expression already includes sensitivity in its denominator, so do not divide UNCERT again.
3. Estimate background as median corrected enhancement outside the vetted plume polygon within the crop (~2.5 km padding). This may contain other sources or surface artifacts; a source-specific upwind region has not been established.
4. Select pixels inside the vetted polygon with corrected-minus-background enhancement ≥500 ppm·m and ≥2 × sensor uncertainty. Sensitivity tests use 1000 and 1500 ppm·m. These choices are screening thresholds, not a calibrated false-positive probability.
5. Compute actual WGS84 geodesic cell areas. Convert enhancement to column mass using `mass_kg = enhancement_ppmm × 1e-6 × methane_molar_mass_kg_mol × pressure_pa / (R × temperature_k) × pixel_area_m2`.
6. Sum selected pixel masses to get integrated excess methane, not a mass emission rate. Independent sensor-noise propagation ignores pixel covariance and mask/background/model systematics.
7. Fetch real ERA5 data through Open-Meteo for 9 June 2024 near the landfill. Bundled original response returns 21.75 N, 39.50 E. Use 05:00 UTC: wind 1.14 m/s from 105°, temperature 310.95 K, pressure 98870 Pa. Surface P/T approximate plume conditions. The response is cached for offline reproducibility.
8. Calculate a **diagnostic whole-complex scenario** `Q_kg_h = 3600 × wind_m_s × integrated_mass_kg / fetch_m`, where fetch is maximum separation of selected pixel centres in UTM 37N. This differs from NASA's origin-seeded source mask. An assumed wind error floor `max(1.5 m/s, 50% of speed)` is propagated with sensor noise; the resulting partial sigma is not a complete confidence interval.

## Findings and interpretation

At the primary mask: 812 selected pixels, ~2.74 km², integrated excess CH4 ~2219.7 kg, maximum raw enhancement 4475.8 ppm·m. The diagnostic scenario is ~768 kg/h with partial assumed 1σ ~1011 kg/h. At 1500 ppm·m the scenario falls to ~242 kg/h, showing substantial mask sensitivity.

**No validated or attributed landfill emission rate is reported.** NASA supplied no wind, rate, fetch or manually identified source origin in this GeoJSON. The selected whole-complex span is ~11.86 km; multiple/extended sources and coarse low winds violate or leave unverified important single-source Simple-IME assumptions. The footprint is approximately north–south whereas returned wind points toward 285°, adding a qualitative inconsistency. No landfill boundary or independent operational evidence has been supplied. These scenarios must remain out of Scope 1 and annual CO2e totals. A ground/local wind measurement, identified source origin and appropriate connected source mask are the next validation inputs.

The real plume pixels can still demonstrate pollutant mapping and uncertainty-aware screening. The other sites remain at their previously documented coverage state; this update does not fabricate pixels for them.

## Sources

- [NASA EMIT greenhouse-gas ATBD](https://github.com/emit-sds/emit-sds-tgp/blob/develop/docs/EMIT_L2B_TRACE_GAS_ATBD.md): sensitivity, sensor uncertainty, Simple IME, source assumptions and exclusions.
- [NASA EMIT user guide](https://github.com/emit-sds/emit-sds-tgp/blob/develop/docs/EMIT_L2B_TRACE_GAS_User_Guide.md): file structure and units.
- [Open-Meteo historical API](https://open-meteo.com/en/docs/historical-weather-api): ERA5 historical weather access.

## Seropédica observations added

`python -m src.emit_cases` now processes Jeddah plus 5 March and 24 September 2024 at CTR Santa Rosa. Brazil uses original NASA PLM rasters and vetted GeoJSON polygons. No companion uncertainty/sensitivity rasters were supplied, so Brazil is analyzed as raw plume enhancement with no sensitivity correction, background subtraction or SNR filter. These differences are shown explicitly in the dashboard. Thresholds 500, 1000 and 1500 ppm·m assess mask sensitivity. WGS84 areas and ideal-gas mass conversion use ERA5 pressure/temperature, and wind vectors are interpolated between the two adjacent hourly samples. Diagnostic Simple-IME is whole-complex only; no validated source rate or confidence interval is claimed.

| Event | Peak raw ppm·m | ERA5 wind m/s | Selected pixels at 500 | Integrated excess CH4 kg | Diagnostic flux kg/h |
|---|---:|---:|---:|---:|---:|
| Jeddah 2024-06-09 | 4476 | 1.14 | 812 | 2220 | 768 |
| Seropédica 2024-03-05 | 11076 | 1.94 | 2084 | 6413 | 7764 |
| Seropédica 2024-09-24 | 2511 | 2.73 | 747 | 1399 | 2885 |

Mass values are selected snapshot excess mass, not emissions per hour. Processing levels differ, so direct inter-site comparisons require the same corrections and selection criteria. Diagnostic flux is particularly sensitive to thresholds and incomplete source geometry. All attributed facility rates remain null. The website presents completed observations only; unexecuted optional methane/CO2 case panels have been removed, without representing them as measurements.

Source scenes from the uploaded GeoJSON:
- March: `EMIT_L2B_CH4ENH_V002_20240305T123325_2406508_014`
- September: `EMIT_L2B_CH4ENH_V002_20240924T133617_2426808_018`

These companion source products are optional next inputs for harmonizing Brazil with the Jeddah sensitivity/uncertainty workflow. They are not a prerequisite to reproduce the bundled PLM pixel analyses.
