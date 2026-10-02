# EcoOrbit | Methane-first GRI 305 evidence assessment (research pilot)

**Boundary:** 24 EPA TRI-associated points in three US cities with observed Tanager spectra; 424 additional EPA registry candidates await image QA, site geometry and operating checks. Satellite observations do not establish ownership, a reporting boundary, compliance, a stack plume or a mass emission rate.

## Published real plume examples

The dashboard includes source-linked Tanager CH4 from Brazil's Seropédica landfill (29 Sep 2024, preliminary 2,836 kg/h), Tanager CO2 from Singrauli electricity generation (1 Nov 2024, preliminary source rate 838,000 kg/h), and a Carbon Mapper EMIT CH4 API example (20 Apr 2024, 3,610.58 ± 377.95 kg/h). Source IDs, rate basis and image links are in `data/published_plumes.csv`. These are different locations from the three requested targets. A published spot/source rate is not the organization's reporting-period inventory.

## Methane and pollutant evidence priority

The primary case register includes a documented 2022 Stanford controlled-release experiment, a published Hassi R'Mel 2020 regional methane study, and a Jeddah landfill investigation target. The user-suggested 2024 Jeddah dates and 2024–25 Stanford release period are **not confirmed events** in this package. No case-specific XCH4 or hyperspectral plume granule is included. `src/methane_cases.py` retrieves QA-valid Sentinel-5P regional columns; `src/import_methane_plumes.py` imports separately downloaded Carbon Mapper plume records. A nearby column contrast or plume location requires wind, scene coverage, quality, source geometry and independent corroboration before attribution.

A Carbon Mapper instantaneous plume rate in kg CH4/hour, if supplied and valid, cannot be extrapolated to annual Scope 1 without observed persistence and operational records. Detection absence without clear coverage is not a measured zero.

## Supporting land-use screen and uncertainty

The supplementary factory-versus-school screen uses 36 training and 12 held-out sites, with two sites of each class in every city. Training-only cross-validation selected 8 PCA components. Test accuracy is 0.917 (11/12); ROC AUC is 0.944. Schools contribute a clearly mapped built-environment comparison, but they do not represent all nonindustrial land uses. This small, weakly labeled test cannot validate general factory identification. A model trained on all 48 sites supplies dashboard exploration; its own scores are not test evidence.

## Carbon dioxide and carbon-equivalent evidence

Optional Carbon Mapper CO2 plume records carry instantaneous **kg CO2/hour** and uncertainties; CH4 plumes carry **kg CH4/hour**. Neither is annual tCO2e. No facility ledger has been supplied; Scope 1/2 tCO2e remain unavailable. `src.carbon_results` calculates each period's Scope 1 and Scope 2 metric tonnes CO2e as activity times a documented kgCO2e-per-unit factor divided by 1000. It does not assume a methane GWP or extrapolate a satellite plume. An organization must supply the factor source, activity evidence, boundary and period.

## Standards and evidence mapping

| Topic | International disclosure | Available indicator | Disclosure status and missing evidence |
|---|---|---|---|
| Direct greenhouse gases | GRI 305-1; GHG Protocol Scope 1 | Regional CH4 satellite column; optional CH4/CO2 plume export; optional activity ledger | **Cannot calculate tCO2e**. Need organizational boundary, fuel and process activity, source-specific factors, gas-specific GWP, dates and assurance. Regional CH4 is context only. |
| Purchased energy | GRI 305-2; GHG Protocol Scope 2 | No utility ledger | **Cannot calculate tCO2e**. Need metered electricity/heat, grid and contractual factors, market/location method. |
| NOx, SOx and other significant air emissions | GRI 305-7 | QA-filtered TROPOMI NO2/SO2 atmospheric column; CAMS model context; ERA5 wind | **Cannot calculate kg or tonnes by facility**. Need stack or ground measurements, flow and operating hours, or defensible activity factors; account for upwind sources and uncertainty. Column mol/m² is not a mass emission. |
| Local environment (supplemental) | Not a GRI 305 emission quantity | Landsat surface temperature; Sentinel-2 NDVI/NDBI and AOT | Observed context only; season, surface cover and nearby sources confound attribution. |
| Water and waste | GRI 303 and GRI 306 | No facility inventory | No quantitative disclosure supported. |

**When facility records are supplied:** Scope 1 tCO2e = sum(activity by fuel/process × documented emission factor × GWP where needed). Scope 2 tCO2e = purchased energy × applicable documented factor, with separate location-based and market-based presentation when applicable. GRI 305-7 mass = measured concentration × stack flow × operating time with consistent units, or justified source-specific factors and uncertainty. Do not convert the supplied satellite column into any of these quantities.

## Observed green reference

The archived Jacksonville Tanager material grid yields 12 separated, QA-valid vegetation-rich image patches. Its green spectral cluster has median NDVI **0.770**, versus **0.305** for eight measured industrial-site neighborhoods (difference +0.465). These are different spatial supports: the green statistic is a cluster-wide pixel median, not 12 independent park-site observations. This contrast checks vegetation confounding and does not demonstrate an emission impact or enter classifier testing. Source: `green_reference_summary.json` and `green_reference_patches.csv`.

## Interpretation

Use wind direction, background comparison, repeat dates, and in-situ or stack monitoring to investigate a hypothesis. No source attribution or causal inference is made in this pilot. This is an evidence-gap mapping against international disclosures, not a compliant GRI report. GRI 102/103 (2025) climate and energy standards become effective in 2027; this 2026 pilot uses the GRI 305 topic structure.
