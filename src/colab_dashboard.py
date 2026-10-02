"""Notebook-native viewer for bundled observed EcoOrbit results (no web server)."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ['CH4 and CO2 plumes', 'Methane cases', 'NO2 and SO2', 'Heat', 'Factory classifier', 'Green reference', 'Aerosols and wind', 'ESG evidence']

def _read(path):
    return pd.read_csv(ROOT / path)

def _table(frame, columns=None, limit=30):
    if columns:
        frame = frame[[c for c in columns if c in frame.columns]]
    display(frame.head(limit))
    if len(frame) > limit:
        print(f'Showing {limit} of {len(frame)} records; full CSV is in the project.')

def show_section(section='CH4 and CO2 plumes', city='All', gas='CH4', pollutant='NO2'):
    """Display one section; callable directly even if Colab widgets do not load."""
    display(Markdown('### ' + section))
    if section == 'CH4 and CO2 plumes':
        d = _read('data/published_plumes.csv'); d = d[d.gas == gas]
        _table(d, ['plume_id','site_name','country','gas','scene_timestamp','reported_rate_kg_h','emission_uncertainty_kg_h','wind_speed_m_s','source_url','image_url'])
        if not d.empty:
            ax = d.plot.bar(x='site_name', y='reported_rate_kg_h', legend=False, figsize=(7,3), color='#247c7a')
            ax.set_ylabel('Published source rate (kg/h)'); ax.set_xlabel(''); plt.xticks(rotation=20, ha='right'); plt.tight_layout(); plt.show()
        display(Markdown('Published plume examples are separate from the three proposed methane case sites. Source image links are in the table.'))
    elif section == 'Methane cases':
        _table(_read('results/real/methane/case_status.csv'))
        _table(_read('results/real/methane/observed_us_regional_ch4.csv'))
        display(Markdown('Regional CH4 columns do not identify a facility emission. Case-specific plume evidence must be supplied before attribution.'))
    elif section == 'NO2 and SO2':
        d = _read('results/real/pollutants/site_no2_so2.csv')
        if city != 'All': d = d[d.city == city]
        d = d[d['product'].astype(str).str.upper().eq(pollutant)]
        _table(d, ['city','name','date','product','column_mol_m2','qa','status','nearest_pixel_center_km'], 48)
        valid = d[pd.to_numeric(d.column_mol_m2, errors='coerce').notna()]
        if not valid.empty:
            ax = valid.groupby('city').column_mol_m2.median().plot.bar(figsize=(6,3), color='#9c654b')
            ax.set_ylabel('Median observed column (mol/m²)'); plt.xticks(rotation=0); plt.tight_layout(); plt.show()
        display(Markdown('Sentinel-5P columns are regional context, not facility-level emission rates. Missing QA coverage remains missing.'))
    elif section == 'Heat':
        d = _read('results/real/heat/site_heat.csv')
        if city != 'All': d = d[d.city == city]
        _table(d, ['city','name','date','surface_c','reference_c','surface_excess_c'], 38)
        if not d.empty:
            ax = d.groupby('city').surface_excess_c.median().plot.bar(figsize=(6,3), color='#c86937')
            ax.set_ylabel('Median surface excess (°C)'); plt.xticks(rotation=0); plt.tight_layout(); plt.show()
        display(Markdown('Landsat surface temperature is not a stack temperature or a greenhouse-gas measurement.'))
    elif section == 'Factory classifier':
        _table(_read('results/real/classifier/all_city_test_predictions.csv'), limit=48)
        display(Markdown('Held-out site predictions span the cities. Training labels distinguish industrial sites from comparison sites; inspect the split and metrics in results/real/classifier.'))
    elif section == 'Green reference':
        _table(_read('results/real/green_reference_patches.csv'))
        _table(_read('results/real/spectral_clusters.csv'), ['cluster','name','pixels','ndvi','ndbi'])
        display(Markdown('Green patches are a land-cover reference, not a clean-air measurement.'))
    elif section == 'Aerosols and wind':
        d = _read('results/real/aot/multicity_aot_comparison.csv')
        if city != 'All': d = d[d.city == city]
        _table(d, ['city','name','date','near_aot','reference_aot','difference','wind_speed_kmh','wind_from_deg','downwind_minus_upwind','directional_status'], 30)
        w = _read('results/real/wind_by_city.csv')
        if city != 'All': w = w[w.city == city]
        _table(w.groupby('city',as_index=False).agg(mean_wind_speed_10m=('wind_speed_10m','mean')))
        display(Markdown('AOT is aerosol optical thickness, not a speciated pollutant or proof of source attribution.'))
    elif section == 'ESG evidence':
        _table(_read('data/facility_activity_template.csv'))
        display(Markdown('The GRI-aligned report and source records are in results/ and docs/. Activity and fuel data are required to calculate Scope 1/2 emissions. Satellite observations are screening evidence.'))
    else:
        raise ValueError(f'Unknown section: {section}')

def show_dashboard():
    import ipywidgets as widgets
    section = widgets.Dropdown(options=SECTIONS, description='View:')
    city = widgets.Dropdown(options=['All','Jacksonville','Rochester','Detroit'], description='City:')
    gas = widgets.Dropdown(options=['CH4','CO2'], description='Gas:')
    pollutant = widgets.Dropdown(options=['NO2','SO2'], description='Column:')
    out = widgets.interactive_output(show_section, {'section':section, 'city':city, 'gas':gas, 'pollutant':pollutant})
    display(widgets.VBox([widgets.HBox([section,city]), widgets.HBox([gas,pollutant]), out]))
    print('If controls do not render, run: from src.colab_dashboard import show_section; show_section("Heat")')
